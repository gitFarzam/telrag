#!/bin/sh

# Exit on error
set -e

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