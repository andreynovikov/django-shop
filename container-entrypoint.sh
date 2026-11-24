#!/bin/sh
set -eu

runtime_uid=${STOREFRONT_UID:-}
runtime_gid=${STOREFRONT_GID:-}
set -- /usr/local/bin/docker-entrypoint.sh "$@"

if [ -z "$runtime_uid$runtime_gid" ]; then
  [ "$(id -u)" -eq 0 ] || exec "$@"
  runtime_uid=node
  runtime_gid=node
  export HOME=/home/node
else
  for runtime_id in "$runtime_uid" "$runtime_gid"; do
    case "$runtime_id" in
      ''|0*|*[!0-9]*)
        echo 'STOREFRONT_UID and STOREFRONT_GID must both be positive numeric IDs' >&2
        exit 1
        ;;
    esac
  done

  # Next writes image and fetch caches under .next/cache and regenerated responses under .next/server/route-cache.
  mkdir -p .next/cache .next/server/route-cache
  chown -hR "$runtime_uid:$runtime_gid" .next/cache .next/server/route-cache
  export HOME=/tmp
fi

exec setpriv --reuid="$runtime_uid" --regid="$runtime_gid" --clear-groups --no-new-privs "$@"
