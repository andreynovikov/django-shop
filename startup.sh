#!/bin/sh
set -e

# The image has no configuration of its own: the server mounts it as .env.local (see the Dockerfile), and Next.js
# would start without API_SERVER and the keys if it couldn't read it.
if [ ! -r ./.env.local ]; then
  printf >&2 'Cannot read /app/.env.local as UID:GID %s:%s: mount the storefront configuration there\n' \
    "$(id -u)" "$(id -g)"
  exit 1
fi

# Check existing directories before copying or pruning anything in the nginx asset mount.
if [ -d ./.docker ]; then
  blocked_dir=$(find ./.docker -type d \( ! -readable -o ! -writable -o ! -executable \) -print -quit)
  if [ -n "$blocked_dir" ]; then
    printf >&2 'Cannot sync assets in %s as UID:GID %s:%s (directory mode and owner: %s)\n' \
      "$blocked_dir" "$(id -u)" "$(id -g)" "$(stat -c '%a %u:%g' "$blocked_dir")"
    exit 1
  fi
fi

# Copy a build's files into .docker/, where nginx serves them from, over the previous build's instead of emptying
# the folder first: a file both builds have, such as unavailable.html (nginx's page for when this container is
# down), never disappears. Then delete what this build doesn't have.
# If the copy fails, e.g. because a file became a folder, fall back to replacing the folder as a whole.
sync() { # $1: the source, $2: its copy in .docker/
  if mkdir -p "$2" && cp -a "$1/." "$2/"; then
    (cd "$2" && find . ! -type d) | while IFS= read -r f; do
      [ -e "$1/$f" ] || [ -L "$1/$f" ] || rm -f "$2/$f"
    done
    find "$2" -mindepth 1 -type d -empty -delete
  else
    rm -rf "$2"
    cp -a "$1" "$2"
  fi
}

sync ./.next/static ./.docker/static
sync ./public ./.docker/public
find ./.docker/ -mindepth 1 -maxdepth 1 ! -name static ! -name public -exec rm -rf {} +

# exec replaces the shell, so the signals of docker stop reach node and Next shuts down cleanly
exec node ./server.js
