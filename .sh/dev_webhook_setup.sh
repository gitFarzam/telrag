#!/bin/sh

# Exit on error
set -e


# Setting webhook
# source ./.env (have this commented if .env is already exported in the makefile)

echo ".................... Setting Development Webhook ....................."
echo $DEV_WEBHOOK_ADDRESS
echo ".........................................."

curl -X POST "https://api.telegram.org/bot${TELEGRAM_DEV_API_KEY}/setWebhook" \
  -d "url=${DEV_WEBHOOK_ADDRESS}" \
  -d "secret_token=${TELEGRAM_DEV_WEBHOOK_SECRET}"

echo "End of operation"

echo ".........................................."
echo "⚠️⚠️ Telegram webhooks can only work through ngrok tunneling. Make sure ngrok is installed on your machine and is routing HTTP traffic to the app's exposed port (8000). ⚠️⚠️"

exit "$@"

