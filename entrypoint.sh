#!/bin/sh

# Exit on error
set -e

echo "🧱 Collecting static files..."

# Ensure we're in the Django project directory where manage.py lives
cd /usr/src/app/src

python manage.py collectstatic --noinput

echo "📦 Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Hand off to the container's main command (e.g. daphne, celery)
echo "Running daphne"
exec daphne -b 0.0.0.0 -p 8006 django_project.asgi:application