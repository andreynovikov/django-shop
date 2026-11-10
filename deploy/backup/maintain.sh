#!/bin/bash
# Alarms, retention and restore tests for the restic repository that `manage.py backup_db` fills, see DEPLOYMENT.rst.
# It runs on the backup host with full access to the repository, which is append-only for the production server.
#
#   maintain.sh fresh    hourly: alarm when snapshots stop coming
#   maintain.sh prune    daily: forget the snapshots that the retention policy drops and free their space
#   maintain.sh verify   weekly: read back a part of the data and test a restore of every database
#
# Settings come from /etc/default/db-backup, or the file in DB_BACKUP_SETTINGS, and the environment:
#   RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE   the repository, a local path rather than the rest-server URL
#   DB_HOSTS          restic hosts of database snapshots (DB_BACKUP HOST), separated by spaces
#   CONFIG_HOSTS      restic hosts of config snapshots (DB_BACKUP CONFIG_HOST), separated by spaces
#   ALERT_EMAIL       who gets the alarms by mail(1), or else
#   ALERT_CMD         a shell command that gets the subject as $1 and the text on stdin
#   PGHOST, PGUSER, ...   the PostgreSQL server for restore tests, the user must be able to create databases
#   KEEP_FULL, KEEP_HOT, KEEP_CONFIG, *_MAX_AGE_HOURS, CHECK_SUBSET   see their defaults below
set -euo pipefail

DB_BACKUP_SETTINGS=${DB_BACKUP_SETTINGS:-/etc/default/db-backup}
if [ -f "$DB_BACKUP_SETTINGS" ]; then
    set -a  # restic and restore.sh read the settings from the environment
    . "$DB_BACKUP_SETTINGS"
    set +a
fi

# restic forget options for each kind of snapshot
KEEP_FULL=${KEEP_FULL:---keep-daily 14 --keep-weekly 8 --keep-monthly 12}
KEEP_HOT=${KEEP_HOT:---keep-within 48h}  # counted back from the newest hot snapshot, not from now
KEEP_CONFIG=${KEEP_CONFIG:---keep-daily 14 --keep-monthly 12}
# alarm when the newest snapshot is older
DB_MAX_AGE_HOURS=${DB_MAX_AGE_HOURS:-2}
FULL_MAX_AGE_HOURS=${FULL_MAX_AGE_HOURS:-26}
CONFIG_MAX_AGE_HOURS=${CONFIG_MAX_AGE_HOURS:-50}
# the share of the data that a weekly check reads back
CHECK_SUBSET=${CHECK_SUBSET:-10%}
CONFIG_HOSTS=${CONFIG_HOSTS:-}
DIR=$(dirname "$(readlink -f "$0")")

usage() {
    sed -n '2,/^$/s/^# \{0,1\}//p' "$0" >&2
    exit 2
}

# restic times look like 2026-11-10T03:00:05.123456789+03:00, which jq's fromdateiso8601 does not read
EPOCH='def epoch: capture("^(?<dt>[0-9-]+T[0-9:]+)(\\.[0-9]+)?(?<tz>Z|[+-][0-9]{2}:[0-9]{2})$")
    | (.dt + "Z" | fromdateiso8601) - (if .tz == "Z" then 0
        else (if .tz[0:1] == "-" then -1 else 1 end) * ((.tz[1:3] | tonumber) * 3600 + (.tz[4:6] | tonumber) * 60) end);'

# Print a problem and fail when the newest snapshot of host $1 with any of the tags $4... is older than $2 hours
stale() {
    local host=$1 max=$2 kind=$3 tags=() tag hours
    shift 3
    for tag; do tags+=(--tag "$tag"); done
    hours=$(restic snapshots --json --host "$host" "${tags[@]}" | jq -r --argjson now "$(date +%s)" "$EPOCH"'
        map(.time | epoch) | max // empty | ($now - .) / 3600 | floor')
    if [ -z "$hours" ]; then
        echo "$host has no $kind snapshots"
        return 1
    elif [ "$hours" -ge "$max" ]; then
        echo "The newest $kind snapshot of $host is $hours hours old"
        return 1
    fi
}

fresh() {
    local status=0 host
    for host in $DB_HOSTS; do
        stale "$host" "$DB_MAX_AGE_HOURS" database full hot || status=1
        stale "$host" "$FULL_MAX_AGE_HOURS" full full || status=1
    done
    for host in $CONFIG_HOSTS; do
        stale "$host" "$CONFIG_MAX_AGE_HOURS" config config || status=1
    done
    return $status
}

prune() {
    # the KEEP_* values are lists of options
    # shellcheck disable=SC2086
    {
        restic forget --retry-lock 1h --tag full $KEEP_FULL
        restic forget --retry-lock 1h --tag hot $KEEP_HOT
        restic forget --retry-lock 1h --tag config $KEEP_CONFIG
    }
    restic prune --retry-lock 1h
}

verify() {
    local status=0 host
    restic check --retry-lock 1h --read-data-subset="$CHECK_SUBSET"
    for host in $DB_HOSTS; do
        "$DIR/restore.sh" --host "$host" --target "restore_test_${host//[^a-zA-Z0-9_]/_}" --verify || status=1
    done
    return $status
}

case ${1:-} in
    fresh | prune | verify) ;;
    *) usage ;;
esac
DB_HOSTS=${DB_HOSTS:?set DB_HOSTS, see $0}
[ -n "${ALERT_CMD:-}" ] || ALERT_CMD='mail -s "$1" "$ALERT_EMAIL"'
export ALERT_EMAIL=${ALERT_EMAIL:-}

LOG=$(mktemp)
trap 'rm -f "$LOG"' EXIT
# set -e does not work in a command whose status is tested, so the status is taken afterwards
set +e
(set -e; "$1") > "$LOG" 2>&1
status=$?
set -e
cat "$LOG"
if [ $status -ne 0 ]; then
    tail -n 200 "$LOG" | sh -c "$ALERT_CMD" alert "Database backup: $1 failed on $(hostname)"
fi
exit $status
