#!/bin/bash
# Restore a database from the restic repository that `manage.py backup_db` fills, see DEPLOYMENT.rst.
#
#   restore.sh --host HOST --target DBNAME [--at 'YYYY-MM-DD HH:MM'] [--jobs N] [--verify]
#
#   --host     restic host of the database snapshots: DB_BACKUP HOST, the database name by default
#   --target   the database to create and fill, it must not exist
#   --at       restore the state at this time instead of the latest one
#   --jobs     parallel pg_restore jobs, 2 by default
#   --verify   check the restored data and drop the database, the weekly restore test
#
# The latest full snapshot at or before --at is restored, and the rows of its hot tables are taken from the latest
# hot snapshot after it with the same schema. restic finds the repository in its environment (RESTIC_REPOSITORY,
# RESTIC_PASSWORD_FILE), the libpq tools find the target server in theirs (PGHOST, PGUSER, ...). The dumps are
# unpacked into TMPDIR, which needs room for an uncompressed full dump. Needs restic, jq and PostgreSQL client tools
# of the version that made the dumps or later.
set -euo pipefail

usage() {
    sed -n '2,/^$/s/^# \{0,1\}//p' "$0" >&2
    exit 2
}

HOST='' TARGET='' AT='' JOBS=2 VERIFY=''
while [ $# -gt 0 ]; do
    case $1 in
        --host) HOST=$2; shift 2 ;;
        --target) TARGET=$2; shift 2 ;;
        --at) AT=$2; shift 2 ;;
        --jobs) JOBS=$2; shift 2 ;;
        --verify) VERIFY=1; shift ;;
        *) usage ;;
    esac
done
[ -n "$HOST" ] && [ -n "$TARGET" ] || usage
AT_EPOCH=$(date -d "${AT:-now}" +%s)
# the newest order of a restored database must be at most this old against its snapshot
VERIFY_MAX_ORDER_AGE_HOURS=${VERIFY_MAX_ORDER_AGE_HOURS:-48}

# restic times look like 2026-11-10T03:00:05.123456789+03:00, which jq's fromdateiso8601 does not read
EPOCH='def epoch: capture("^(?<dt>[0-9-]+T[0-9:]+)(\\.[0-9]+)?(?<tz>Z|[+-][0-9]{2}:[0-9]{2})$")
    | (.dt + "Z" | fromdateiso8601) - (if .tz == "Z" then 0
        else (if .tz[0:1] == "-" then -1 else 1 end) * ((.tz[1:3] | tonumber) * 3600 + (.tz[4:6] | tonumber) * 60) end);'

# Print "id epoch time schema-tag" of the latest snapshot that has all the tags and was taken after $2 up to $3
latest() {
    restic snapshots --json --host "$HOST" --tag "$1" | jq -r --argjson after "$2" --argjson at "$3" "$EPOCH"'
        map(. + {epoch: (.time | epoch)} | select(.epoch > $after and .epoch <= $at)) | max_by(.epoch) // empty
        | "\(.id) \(.epoch) \(.time) \([.tags[] | select(startswith("schema:"))][0])"'
}

FULL=$(latest full 0 "$AT_EPOCH")
read -r FULL_ID FULL_EPOCH FULL_TIME SCHEMA <<< "$FULL"
if [ -z "$FULL_ID" ]; then
    echo "No full snapshot of $HOST at or before $(date -d "@$AT_EPOCH")" >&2
    exit 1
fi
HOT=$(latest "hot,$SCHEMA" "$FULL_EPOCH" "$AT_EPOCH")
read -r HOT_ID HOT_EPOCH HOT_TIME _ <<< "$HOT"
echo "Full snapshot ${FULL_ID:0:8} of $FULL_TIME" >&2
[ -z "$HOT_ID" ] || echo "Hot snapshot ${HOT_ID:0:8} of $HOT_TIME" >&2

WORK=$(mktemp -d "${TMPDIR:-/tmp}/restore.XXXXXX")
drop_verified() {
    [ -z "$VERIFY" ] || PGOPTIONS='-c client_min_messages=warning' dropdb --if-exists "$TARGET"
}
cleanup() {
    rm -rf "$WORK"
    drop_verified
}
trap cleanup EXIT
drop_verified  # left over by a test that was killed

restic dump "$FULL_ID" /full.pgdump > "$WORK/full.pgdump"
[ -z "$HOT_ID" ] || restic dump "$HOT_ID" /hot.pgdump > "$WORK/hot.pgdump"
createdb "$TARGET"

FAILED=()
# pg_restore goes on after an error and fails at the end, so every step runs and the failed ones are listed
step() {
    local name=$1
    shift
    echo "== $name" >&2
    "$@" || FAILED+=("$name")
}
RESTORE=(pg_restore --no-owner --no-privileges --dbname="$TARGET" --jobs="$JOBS")

# Tables and sequences, without indexes and constraints, so that the hot rows can replace the full ones
step 'schema' "${RESTORE[@]}" --section=pre-data "$WORK/full.pgdump"
if [ -n "$HOT_ID" ]; then
    HOT_TABLES=$(pg_restore --list "$WORK/hot.pgdump" | awk '$4 == "TABLE" && $5 == "DATA" { print $6 "." $7 }')
    pg_restore --list "$WORK/full.pgdump" | awk -v hot="$HOT_TABLES" '
        BEGIN { split(hot, tables, "\n"); for (i in tables) skip[tables[i]] = 1 }
        !($4 == "TABLE" && $5 == "DATA" && ($6 "." $7) in skip)' > "$WORK/full.list"
    step 'full data' "${RESTORE[@]}" --section=data --use-list="$WORK/full.list" "$WORK/full.pgdump"
    step 'hot data' "${RESTORE[@]}" --data-only "$WORK/hot.pgdump"
else
    HOT_TABLES=''
    step 'full data' "${RESTORE[@]}" --section=data "$WORK/full.pgdump"
fi
# A foreign key fails here when a hot row points at a row the full dump does not have, such as a product made
# after it. That constraint is then missing, the rest of the restore is fine.
step 'indexes and constraints' "${RESTORE[@]}" --section=post-data "$WORK/full.pgdump"
step 'analyze' psql -X -q -d "$TARGET" -c 'ANALYZE'

if [ -n "$VERIFY" ]; then
    query() { psql -X -At -v ON_ERROR_STOP=1 -d "$TARGET" -c "$1"; }
    for table in $HOT_TABLES; do
        echo "$table: $(query "SELECT count(*) FROM $table") rows" >&2
    done
    SNAPSHOT_EPOCH=${HOT_EPOCH:-$FULL_EPOCH}
    NEWEST=$(query 'SELECT coalesce(extract(epoch FROM max(created)), 0)::bigint FROM shop_order') || NEWEST=0
    if [ "$NEWEST" -lt $((SNAPSHOT_EPOCH - VERIFY_MAX_ORDER_AGE_HOURS * 3600)) ]; then
        echo "The newest order is older than $VERIFY_MAX_ORDER_AGE_HOURS hours before the snapshot" >&2
        FAILED+=('verify')
    fi
fi

if [ ${#FAILED[@]} -gt 0 ]; then
    echo "Restore of $TARGET failed in: ${FAILED[*]}" >&2
    if [[ " ${FAILED[*]} " == *' indexes and constraints '* ]]; then
        echo 'A foreign key that fails above is not created. Fix or delete the rows its DETAIL names, then run the' \
            'ALTER TABLE shown after "Command was".' >&2
    fi
    exit 1
fi
echo "Restored $TARGET" >&2
