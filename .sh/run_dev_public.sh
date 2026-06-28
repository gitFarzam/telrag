#!/bin/sh

# Exit on error
set -e

echo "Docker | Pruning"
docker compose -f ./compose.dev.yaml down
echo "Deleting app, celery, flower images"
docker rmi telrag-app telrag-celery telrag-flower

echo "Pruning all caches?"
docker builder prune --all

echo "Deleting all unused images? (Online images also will be pulled again)"
docker image prune -a


echo "Docker | Building"
docker compose -f ./compose.dev.yaml build 
docker compose -f ./compose.dev.yaml --profile public up -d

echo "⚠️ App is now publicly accessible on the internet through ngrok tunneling. ⚠️"

exit "$@"