#!/bin/sh
set -e

find ./.docker/ -mindepth 1 -delete
cp -a ./.next/static ./.docker/
cp -a ./public ./.docker/
# exec replaces the shell, so the signals of docker stop reach node and Next shuts down cleanly
exec node "$APP_MAIN_FILE"
