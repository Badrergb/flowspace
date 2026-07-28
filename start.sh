#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
# Use host 0.0.0.0 and dynamically bind to the PORT environment variable if provided by the host (default to 8000)
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
