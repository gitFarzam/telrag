#!/bin/sh

# Exit on error
set -e


# Setting webhook
# . works like source , source is a bash command , but in vps we have shell, . works anyone if is available

# no need to source env here! docker compose will do it automatically!

if [ "${DEBUG:-0}" -eq 1 ]; then
  webhook_address=$ONLINE_WEBHOOK_ADDRESS
else
  webhook_address=$LOCAL_WEBHOOK_ADDRESS
fi

curl -X POST "https://api.telegram.org/bot${TELEGRAM_API_KEY}/setWebhook" \
  -d "url=${webhook_address}" \
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