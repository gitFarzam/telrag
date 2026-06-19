#!/bin/sh

# Exit on error
set -e
 
echo "🧱 Collecting static files..."

# Ensure we're in the Django project directory where manage.py lives
# Change to directory where manage.py is
cd /usr/src/app/src || exit 1
python manage.py collectstatic --noinput

# Migrations
echo "📦 Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Fininshing message
echo "Finishing entrypint execution"


exec "$@"  # executes CMD from Dockerfile or Compose