#!/bin/sh

# exit on error
set -e

echo "Waiting for Postgres..."
while ! nc -z db 5432; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres started"

echo "Running migrations..."
if alembic upgrade head; then
  echo "Migrations completed successfully"
else
  echo "Migrations failed"
  exit 1
fi

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done

echo "Redis started"

echo "Running Celery"
if celery -A app.celery_task.c_app worker -l info; then
  echo "Started Celery successfully"
else
  echo "Celery failed"
  exit 1
fi

echo "Starting application..."

if [ "$ENVIRONMENT" = "development"]; then
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
