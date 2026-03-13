#!/bin/bash

set -e

NETWORK="telrag_network"
VOLUME="telrag-pgvector-volume"
IMAGE="telrag_image"

# detach mode (true / false)
DETACH=true

if [ "$DETACH" = true ]; then
    DFLAG="-d"
else
    DFLAG=""
fi


echo "Creating network (if not exists)..."
docker network create $NETWORK 2>/dev/null || true

echo "Creating volume (if not exists)..."
docker volume create $VOLUME 2>/dev/null || true

echo "Removing old containers if they exist..."
docker rm -f telrag_pgvector telrag_redis telrag_app telrag_celery 2>/dev/null || true


echo "Building app image..."
docker build -t $IMAGE .


echo "Starting PostgreSQL (pgvector)..."
docker run $DFLAG \
  --name telrag_pgvector \
  --network $NETWORK \
  --restart always \
  --env-file .env \
  -v $VOLUME:/var/lib/postgresql/data \
  -p 5435:5432 \
  pgvector/pgvector:pg16


echo "Starting Redis..."
docker run $DFLAG \
  --name telrag_redis \
  --network $NETWORK \
  --restart always \
  -p 6379:6379 \
  redis:7


echo "Starting Django (Daphne)..."
docker run $DFLAG \
  --name telrag_app \
  --network $NETWORK \
  --restart always \
  --env-file .env \
  -v $(pwd):/usr/src/app \
  -w /usr/src/app/src \
  -p 8006:8006 \
  $IMAGE \
  daphne -b 0.0.0.0 -p 8006 django_project.asgi:application


echo "Starting Celery worker..."
docker run $DFLAG \
  --name telrag_celery \
  --network $NETWORK \
  --env-file .env \
  -v $(pwd):/usr/src/app \
  -w /usr/src/app/src \
  $IMAGE \
  celery -A config worker -l info


echo "Containers started."
