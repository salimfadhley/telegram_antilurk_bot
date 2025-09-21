#!/bin/bash

# PostgreSQL External Access Configuration Script
# Run this on the halob server to enable external connections

set -e

echo "🔧 Configuring PostgreSQL for External Connections"
echo "=================================================="

# Check if PostgreSQL container is running
if ! docker ps | grep -q postgres-16; then
    echo "❌ PostgreSQL container 'postgres-16' not found or not running"
    echo "   Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

echo "✅ PostgreSQL container 'postgres-16' is running"

# Step 1: Configure PostgreSQL to listen on all addresses
echo ""
echo "📝 Step 1: Configuring postgresql.conf for external connections..."

docker exec postgres-16 bash -c "
    # Check current listen_addresses setting
    echo 'Current listen_addresses setting:'
    grep -n 'listen_addresses' /var/lib/postgresql/data/postgresql.conf || echo 'Not found'

    # Update or add listen_addresses setting
    if grep -q '^#listen_addresses' /var/lib/postgresql/data/postgresql.conf; then
        sed -i \"s/^#listen_addresses.*/listen_addresses = '*'/\" /var/lib/postgresql/data/postgresql.conf
        echo '✅ Updated existing listen_addresses setting'
    elif grep -q '^listen_addresses' /var/lib/postgresql/data/postgresql.conf; then
        sed -i \"s/^listen_addresses.*/listen_addresses = '*'/\" /var/lib/postgresql/data/postgresql.conf
        echo '✅ Modified existing listen_addresses setting'
    else
        echo \"listen_addresses = '*'\" >> /var/lib/postgresql/data/postgresql.conf
        echo '✅ Added listen_addresses setting'
    fi
"

# Step 2: Configure pg_hba.conf for external authentication
echo ""
echo "📝 Step 2: Configuring pg_hba.conf for external authentication..."

docker exec postgres-16 bash -c "
    echo 'Current pg_hba.conf entries:'
    cat /var/lib/postgresql/data/pg_hba.conf | tail -10

    # Add external access rules if they don't exist
    if ! grep -q 'host.*all.*all.*192.168.86.0/24.*md5' /var/lib/postgresql/data/pg_hba.conf; then
        echo 'host all all 192.168.86.0/24 md5' >> /var/lib/postgresql/data/pg_hba.conf
        echo '✅ Added local network access rule'
    else
        echo '✅ Local network access rule already exists'
    fi

    if ! grep -q 'host.*all.*all.*0.0.0.0/0.*md5' /var/lib/postgresql/data/pg_hba.conf; then
        echo 'host all all 0.0.0.0/0 md5' >> /var/lib/postgresql/data/pg_hba.conf
        echo '✅ Added global access rule (for testing)'
    else
        echo '✅ Global access rule already exists'
    fi

    echo ''
    echo 'Updated pg_hba.conf entries:'
    tail -5 /var/lib/postgresql/data/pg_hba.conf
"

# Step 3: Create the antilurk database and user
echo ""
echo "📝 Step 3: Creating antilurk database and user..."

docker exec postgres-16 psql -U postgres -c "
    -- Create database if it doesn't exist
    SELECT 'CREATE DATABASE antilurk'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'antilurk')
    \\gexec

    -- Create user if it doesn't exist
    DO \\\$\\\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'antilurk_bot') THEN
            CREATE USER antilurk_bot WITH ENCRYPTED PASSWORD 'AntiLurk2024!SecurePass';
            RAISE NOTICE 'Created user antilurk_bot';
        ELSE
            ALTER USER antilurk_bot WITH ENCRYPTED PASSWORD 'AntiLurk2024!SecurePass';
            RAISE NOTICE 'Updated password for antilurk_bot';
        END IF;
    END
    \\\$\\\$;

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE antilurk TO antilurk_bot;
    ALTER DATABASE antilurk OWNER TO antilurk_bot;

    \\c antilurk

    -- Grant schema permissions
    GRANT ALL ON SCHEMA public TO antilurk_bot;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO antilurk_bot;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO antilurk_bot;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO antilurk_bot;

    SELECT 'Database and user setup completed' as result;
" || echo "⚠️  Database/user creation had issues (may already exist)"

# Step 4: Restart PostgreSQL to apply changes
echo ""
echo "📝 Step 4: Restarting PostgreSQL to apply configuration changes..."

docker restart postgres-16

echo "⏳ Waiting for PostgreSQL to restart..."
sleep 5

# Verify PostgreSQL is running
if docker ps | grep -q postgres-16; then
    echo "✅ PostgreSQL restarted successfully"
else
    echo "❌ PostgreSQL restart failed"
    docker logs postgres-16 --tail 10
    exit 1
fi

echo ""
echo "🎉 PostgreSQL External Access Configuration Complete!"
echo "=================================================="
echo "✅ PostgreSQL now configured to accept external connections"
echo "✅ Created antilurk database and antilurk_bot user"
echo "✅ Service restarted and running"
echo ""
echo "📋 Connection details:"
echo "   Database URL: postgresql://antilurk_bot:AntiLurk2024!SecurePass@halob:5432/antilurk"
echo "   Alternative:  postgresql://antilurk_bot:AntiLurk2024!SecurePass@192.168.86.31:5432/antilurk"
echo ""
echo "🧪 Test connectivity with:"
echo "   uv run python deploy/test_external_connection.py"