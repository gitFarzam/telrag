#!/bin/sh

# Exit on error
set -e


# Setting webhook
source .env

echo ".................... Setting Production Webhook ....................."
echo $ONLINE_WEBHOOK_ADDRESS
echo ".........................................."

curl -X POST "https://api.telegram.org/bot${TELEGRAM_API_KEY}/setWebhook" \
  -d "url=${ONLINE_WEBHOOK_ADDRESS}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"

echo "Webhook has been set"


echo "Docker | Pruning"
docker compose down
docker builder prune --all
docker image prune -a

echo "pulling last changes"
git pull origin demo

echo "Docker | Building"
docker compose build --no-cache
docker compose up -d

exit "$@"