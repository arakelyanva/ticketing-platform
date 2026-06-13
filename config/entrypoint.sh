#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting application initialization..."

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting Uvicorn server..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $FASTAPI_PORT
