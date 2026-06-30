#!/bin/sh

# Exit on error
set -e

echo "Docker | Pruning"
docker compose down

echo "Deleting app, celery, flower images"
docker rmi telrag-app telrag-celery telrag-flower

docker builder prune --all
docker image prune -a

echo "pulling last changes"
# git pull origin main

echo "Docker | Building"
docker compose build --no-cache
docker compose up -d

exit "$@"