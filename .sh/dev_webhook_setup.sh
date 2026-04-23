#!/bin/sh

# Exit on error
set -e


# Setting webhook
source ./.env

echo ".................... Setting Development Webhook ....................."
echo $DEV_WEBHOOK_ADDRESS
echo ".........................................."

curl -X POST "https://api.telegram.org/bot${TELEGRAM_DEV_API_KEY}/setWebhook" \
  -d "url=${DEV_WEBHOOK_ADDRESS}" \
  -d "secret_token=${TELEGRAM_DEV_WEBHOOK_SECRET}"

echo "Webhook has been set"

echo ".........................................."
echo "⚠️⚠️ telegram webhook just can work through ngrok bypassing!!  ⚠️⚠️"

exit "$@"

