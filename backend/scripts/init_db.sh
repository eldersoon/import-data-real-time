#!/bin/bash
# Script to initialize database and run migrations

echo "Running database migrations..."

alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully!"
else
    echo "Failed to run migrations. Check database connection."
    exit 1
fi
