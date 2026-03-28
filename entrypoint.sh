#!/bin/sh

# Exit on error
set -e


# Setting webhook
source .env

curl -X POST "https://api.telegram.org/bot${TELEGRAM_API_KEY}/setWebhook" \
  -d "url=${ONLINE_WEBHOOK_ADDRESS}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"

echo "Webhook has been set"

echo "-> ls"
ls -a

echo "Current Directory"
pwd

echo "🧱 Collecting static files..."

# Ensure we're in the Django project directory where manage.py lives
# Change to directory where manage.py is
cd /usr/src/app/src || exit 1

echo "Current Directory After cd"
pwd

echo "-> ls"
ls -a

python manage.py collectstatic --noinput

echo "📦 Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "finighsing entrypint"

exec "$@"  # executes CMD from Dockerfile or Compose