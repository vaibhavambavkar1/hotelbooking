#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ---------------------------------------------------------------------------
# Wait for MySQL to be ready before attempting migrations.
# Uses DB_HOST and DB_PORT from the environment (set in .env / docker-compose).
# ---------------------------------------------------------------------------
DB_HOST="${DB_HOST:-mysql}"
DB_PORT="${DB_PORT:-3306}"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "  MySQL is not ready yet — sleeping 2s..."
  sleep 2
done
echo "MySQL is up and accepting connections."

echo "Running Database Migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting Static Files..."
python manage.py collectstatic --noinput

# Execute the main command passed to the docker container (e.g. gunicorn)
exec "$@"
