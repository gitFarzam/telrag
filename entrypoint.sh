#!/bin/sh

# Exit on error
set -e

echo "🧱 Collecting static files..."
uv run manage.py collectstatic

echo "📦 Running migrations..."
uv run manage.py makemigrations
uv run manage.py migrate
