#!/bin/sh

# Exit on error
set -e

echo "Docker | Pruning"
docker compose -f ./compose.yaml -f ./compose/compose.production.yaml down
docker builder prune --all
docker image prune -a

echo "pulling last changes"
git pull origin demo

echo "Docker | Building"
docker compose -f ./compose.yaml -f ./compose/compose.production.yaml build --no-cache
docker compose -f ./compose.yaml -f ./compose/compose.production.yaml up -d

exit "$@"