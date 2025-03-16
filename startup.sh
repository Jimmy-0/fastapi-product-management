#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD="postgres" psql -h db -U postgres -d product_service -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - executing application"

# Run database migrations or initialization if needed
python -m app.core.init_db

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000