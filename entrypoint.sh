#!/bin/sh

# Exit on error
set -e

echo "Current Directory"
pwd

echo "🧱 Collecting static files..."

# Ensure we're in the Django project directory where manage.py lives
# cd /usr/src/app/src

echo "Current Directory After cd"
pwd

echo "-> ls"
ls -a

python manage.py collectstatic --noinput

echo "📦 Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "finighsing entrypint"