#!/bin/sh

# Exit on error
set -e


# Setting webhook
source .env

curl -X POST "https://api.telegram.org/bot${TELEGRAM_API_KEY}/setWebhook" \
  -d "url=${LOCAL_WEBHOOK_ADDRESS}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"

echo "Webhook has been set"

echo "running django app"
cd /Users/farzam/work/project/telrag/src
python manage.py runserver

