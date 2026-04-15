#!/bin/sh

# Exit on error
set -e


# Setting webhook
source .env

echo ".................... Setting Development Webhook ....................."
echo $LOCAL_WEBHOOK_ADDRESS
echo ".........................................."

curl -X POST "https://api.telegram.org/bot${TELEGRAM_API_KEY}/setWebhook" \
  -d "url=${LOCAL_WEBHOOK_ADDRESS}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"

echo "Webhook has been set"



echo "Docker | Pruning"
docker compose -f dev-compose.yaml down
docker builder prune --all
docker image prune -a


echo "Docker | Building"
docker compose -f dev-compose.yaml build --no-cache
docker compose -f dev-compose.yaml up



exit "$@"

