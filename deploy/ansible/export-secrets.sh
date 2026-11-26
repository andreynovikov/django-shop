#!/bin/sh
# Reads the secrets of the production server into group_vars/production/secrets.yml, encrypted with ansible-vault,
# which asks for the new vault password. See "Secrets" in README.md.
#
#   ./export-secrets.sh -K --limit server.example.ru
#
# The arguments go to ansible-playbook. The secrets stay in a temporary directory only this user can read, and the
# script deletes it.
set -eu
cd "$(dirname "$0")"
out=group_vars/production/secrets.yml
if [ -e "$out" ]; then
  echo "$out exists already, move it away first" >&2
  exit 1
fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
ansible-playbook -i inventory.yml export-secrets.yml -e "secrets_export_file=$tmp/secrets.json" "$@"
mkdir -p "$(dirname "$out")"
# Multi-line values, the files, as YAML block scalars, so that ansible-vault edit shows them as they are
python3 - "$tmp/secrets.json" "$tmp/inventory.yml" > "$tmp/secrets.yml" <<'PYTHON'
import json
import sys

import yaml


def text(dumper, value):
    return dumper.represent_scalar('tag:yaml.org,2002:str', value, style='|' if '\n' in value else None)


yaml.SafeDumper.add_representer(str, text)
secrets = json.load(open(sys.argv[1]))
inventory = secrets.pop('inventory')
print('# Secrets of the production server, see "Secrets" in deploy/ansible/README.md.')
print('# Change them with: ansible-vault edit group_vars/production/secrets.yml')
print(yaml.safe_dump(secrets, sort_keys=False, allow_unicode=True, width=1000))
with open(sys.argv[2], 'w') as f:
    yaml.safe_dump(inventory, f, sort_keys=False, allow_unicode=True, width=1000)
PYTHON
ansible-vault encrypt --output "$out" < "$tmp/secrets.yml"
echo "The secrets are in $out. These settings of the server go into the vars of production in inventory.yml:"
cat "$tmp/inventory.yml"
