#!/bin/bash

# Stop on error
set -e

# Config (change these)
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
export DJANGO_SUPERUSER_PASSWORD=admin

# Create superuser if it doesn't exist
uv run ../src/manage.py createsuperuser --noinput || true

echo "✅ Admin user ensured"
