#!/bin/sh

# Exit on error
set -e

echo "Docker | Pruning"
docker compose -f dev-compose.yaml down
docker builder prune --all
docker image prune -a


echo "Docker | Building"
docker compose -f dev-compose.yaml build --no-cache
docker compose -f dev-compose.yaml up



exit "$@"

