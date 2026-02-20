#!/bin/bash
# Script to reset database: drop all tables and reapply migrations

set -e

echo "⚠️  WARNING: This will drop all tables and data!"
echo "Resetting database..."

# Check if we're in a Docker container or local
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container..."
    cd /app
else
    echo "Running locally..."
    cd "$(dirname "$0")/.."
fi

# Wait for database to be ready (using Python instead of pg_isready)
echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())
from sqlalchemy import create_engine, text
from app.core.config import settings
try:
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Database is unavailable - sleeping (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Database connection timeout after $MAX_RETRIES attempts"
    exit 1
fi

# Check current revision
CURRENT_REV=$(alembic current 2>/dev/null | awk '{print $1}' || echo "")

if [ -n "$CURRENT_REV" ] && [ "$CURRENT_REV" != "None" ]; then
    echo "Current revision: $CURRENT_REV"
    echo "Downgrading database to base..."
    alembic downgrade base || echo "Warning: Could not downgrade (might already be at base)"
else
    echo "No migrations applied yet (database might be empty)"
fi

# Upgrade to head (recreates all tables)
echo "Upgrading database to head..."
alembic upgrade head

echo "✅ Database reset completed successfully!"
echo "All tables have been dropped and recreated with latest schema."
