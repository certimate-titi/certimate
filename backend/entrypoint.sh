#!/bin/sh

echo "=== CertiMate Backend Startup ==="

# Run Alembic migrations (retry up to 3 times, non-fatal)
echo "Running database migrations..."
RETRY=0
MAX_RETRY=3
while [ $RETRY -lt $MAX_RETRY ]; do
    if python -m alembic upgrade head 2>&1; then
        echo "Migrations complete."
        break
    else
        RETRY=$((RETRY + 1))
        if [ $RETRY -lt $MAX_RETRY ]; then
            echo "Migration attempt $RETRY failed, retrying in 5s..."
            sleep 5
        else
            echo "WARNING: Migrations failed after $MAX_RETRY attempts. Starting server anyway..."
        fi
    fi
done

# Start the server
echo "Starting Uvicorn on port ${PORT:-8080}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
