#!/bin/sh

# Exit on error
set -e

echo "Docker | Pruning"
docker compose -f ./compose.dev.yaml down
docker builder prune --all
docker image prune -a


echo "Docker | Building"
docker compose -f ./compose.dev.yaml build 
docker compose -f ./compose.dev.yaml --profile public up -d

exit "$@"