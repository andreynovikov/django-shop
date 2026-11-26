#!/bin/sh
# Sets up the server it runs on with site.yml, as root. See "Quick setup with Ansible" in deploy/README.md.
#
#   ./setup-server.sh ~/inventory.yml ~/secrets.yml    the first time: puts the two files in place, then runs
#   ./setup-server.sh                                  later, for example after the DNS switch
#
# More arguments go to ansible-playbook, such as --check --diff. It asks for the vault password, unless
# ANSIBLE_VAULT_PASSWORD_FILE names a file with it.
set -eu
cd "$(dirname "$0")"

if [ "$(id -u)" != 0 ]; then
  echo "Run it as root: sudo $0 $*" >&2
  exit 1
fi

case ${1-} in
  '' | -*) ;;
  *)
    if [ $# -lt 2 ] || [ ! -f "$1" ] || [ ! -f "$2" ]; then
      echo "usage: $0 [INVENTORY SECRETS] [ansible-playbook options]" >&2
      exit 2
    fi
    install -m 600 "$1" inventory.yml
    install -D -m 600 "$2" group_vars/production/secrets.yml
    shift 2
    ;;
esac

for file in inventory.yml group_vars/production/secrets.yml; do
  if [ ! -f "$file" ]; then
    echo "No $file: give the inventory and the secrets, $0 INVENTORY SECRETS" >&2
    exit 1
  fi
done

# Ansible becomes other users with sudo, and a minimal Debian has neither
missing=
command -v ansible-playbook >/dev/null || missing="$missing ansible"
command -v sudo >/dev/null || missing="$missing sudo"
if [ -n "$missing" ]; then
  apt-get update
  # shellcheck disable=SC2086
  apt-get install -y $missing
fi

[ -n "${ANSIBLE_VAULT_PASSWORD_FILE-}" ] || set -- --ask-vault-pass "$@"
exec ansible-playbook -i inventory.yml site.yml --limit production --connection local "$@"
