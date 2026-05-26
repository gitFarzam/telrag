#!/bin/sh

# Exit on error
set -e

# Transfering Data file

mv data/ src/

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

# echo "Initial Command For Inserting Data"
# python manage.py insert_data

echo "finighsing entrypint"

exec "$@"  # executes CMD from Dockerfile or Compose