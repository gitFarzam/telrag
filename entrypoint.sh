#!/bin/sh

# Exit on error
set -e

echo "🧱 Collecting static files..."

# Ensure we're in the Django project directory where manage.py lives
cd /usr/src/app/src

uv run manage.py collectstatic --noinput

echo "📦 Running migrations..."
uv run manage.py makemigrations
uv run manage.py migrate

# Hand off to the container's main command (e.g. daphne, celery)
exec "$@"