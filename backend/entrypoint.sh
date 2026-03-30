#!/bin/sh
set -e

echo "=== CertiMate Backend Startup ==="

# Run Alembic migrations
echo "Running database migrations..."
python -m alembic upgrade head
echo "Migrations complete."

# Start the server
echo "Starting Uvicorn on port ${PORT:-8080}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
