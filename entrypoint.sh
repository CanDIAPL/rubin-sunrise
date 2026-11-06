#!/bin/bash
set -e

echo "🐳 Starting Rubin Sunrise containerized application..."

# Ensure tablespace directory exists with correct permissions
echo "📁 Setting up PostgreSQL tablespace directory..."
mkdir -p /var/lib/postgresql/custom_storage
chown postgres:postgres /var/lib/postgresql/custom_storage
chmod 700 /var/lib/postgresql/custom_storage

# Start PostgreSQL service
# Find the PostgreSQL version dynamically
PG_VERSION=$(ls /usr/lib/postgresql/ | tail -1)
sudo -u postgres /usr/lib/postgresql/$PG_VERSION/bin/initdb -D /var/lib/postgresql/data 2>&1 | grep -v "could not change directory" || true

# Start PostgreSQL in the background
sudo -u postgres /usr/lib/postgresql/$PG_VERSION/bin/postgres -D /var/lib/postgresql/data &
POSTGRES_PID=$!

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
for i in {1..30}; do
    if sudo -u postgres psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start after 30 seconds"
        kill $POSTGRES_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Create the default database and user if they don't exist
echo "📝 Setting up database schema..."
sudo -u postgres psql -U postgres << EOF
-- Create root role if it doesn't exist
CREATE ROLE root WITH LOGIN SUPERUSER CREATEDB;

-- Create tablespace for demo
CREATE TABLESPACE rubin_tablespace LOCATION '/var/lib/postgresql/custom_storage';

-- Create database if it doesn't exist
CREATE DATABASE lsst_database TABLESPACE rubin_tablespace;

-- Grant permissions to root user
GRANT ALL PRIVILEGES ON DATABASE lsst_database TO root;
EOF

echo "✓ Database setup complete"

# Export environment to run the app
export PYTHONUNBUFFERED=1
export PGPASSWORD=""

echo "🚀 Starting Rubin Sunrise application on port 8000..."
echo "Running in Docker container: YES ✓"
python -m rubin_sunrise both

# Cleanup: stop PostgreSQL when Flask exits
kill $POSTGRES_PID 2>/dev/null || true
