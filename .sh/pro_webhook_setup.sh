#!/bin/sh

# Exit on error
set -e


# Setting webhook
# source ./.env (have this commented if .env is already exported in the makefile)

echo ".................... Setting Production Webhook ....................."
echo "First, Deleting the current webhook"

curl -X POST "https://api.telegram.org/bot${TELEGRAM_API_KEY}/deleteWebhook" \

echo "Now, setting the new webhook address"
echo $ONLINE_WEBHOOK_ADDRESS
echo ".........................................."

curl -X POST "https://api.telegram.org/bot${TELEGRAM_API_KEY}/setWebhook" \
  -d "url=${ONLINE_WEBHOOK_ADDRESS}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"

echo "End of operation"


exit "$@"

