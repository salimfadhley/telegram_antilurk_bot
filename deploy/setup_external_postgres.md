# External PostgreSQL Connection Setup

This guide helps configure the halob PostgreSQL server to accept external connections for the Telegram Anti-Lurk Bot.

## Issue Diagnosis

The database connection tests are being skipped because PostgreSQL is configured to only accept localhost connections. Network connectivity is working (port 5432 is open), but authentication fails for external connections.

## Required PostgreSQL Configuration Changes

### 1. Update PostgreSQL Configuration

Connect to the halob server and modify PostgreSQL settings:

```bash
# SSH or console access to halob
ssh halob

# Access the PostgreSQL container
docker exec -it postgres-16 bash

# Edit postgresql.conf to allow external connections
echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf

# Edit pg_hba.conf to allow external authentication
echo "host all all 192.168.86.0/24 md5" >> /var/lib/postgresql/data/pg_hba.conf
echo "host all all 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf
```

### 2. Alternative: Docker Configuration

If using docker-compose, update the PostgreSQL service:

```yaml
# In docker-compose.yml or Portainer stack
services:
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    command: >
      postgres -c listen_addresses='*'
               -c max_connections=200
               -c shared_buffers=256MB
```

### 3. Create Bot Database User

```sql
-- Connect to PostgreSQL as superuser
psql -h halob -U postgres -d postgres

-- Create database for the bot
CREATE DATABASE antilurk;

-- Create user for external connections
CREATE USER antilurk_bot WITH ENCRYPTED PASSWORD 'AntiLurk2024!SecurePass';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE antilurk TO antilurk_bot;
ALTER DATABASE antilurk OWNER TO antilurk_bot;

-- Connect to the new database and set permissions
\c antilurk

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO antilurk_bot;
GRANT ALL ON ALL TABLES IN SCHEMA public TO antilurk_bot;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO antilurk_bot;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO antilurk_bot;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO antilurk_bot;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO antilurk_bot;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO antilurk_bot;
```

### 4. Restart PostgreSQL Service

```bash
# Restart the PostgreSQL container to apply configuration changes
docker restart postgres-16

# Verify the service is running
docker ps | grep postgres-16
```

## Test External Connectivity

After configuration, test the connection:

```bash
# Test from external machine (like your development machine)
export DATABASE_URL="postgresql://antilurk_bot:AntiLurk2024!SecurePass@halob:5432/antilurk"
uv run pytest tests/integration/test_database_connection.py::test_halob_postgres_connection -v

# Or test with psql directly
psql "postgresql://antilurk_bot:AntiLurk2024!SecurePass@halob:5432/antilurk" -c "SELECT version();"
```

## Security Considerations

1. **Strong Password**: Use a complex password for the `antilurk_bot` user
2. **Network Restrictions**: Consider limiting connections to specific IP ranges
3. **SSL Encryption**: Enable SSL for production deployments
4. **Firewall Rules**: Ensure only necessary machines can access port 5432

## Troubleshooting Common Issues

### Connection Refused
- Check if PostgreSQL is listening on all interfaces: `netstat -an | grep 5432`
- Verify `listen_addresses = '*'` in postgresql.conf

### Authentication Failed
- Verify user exists: `\du antilurk_bot` in psql
- Check pg_hba.conf has proper authentication method (md5)
- Ensure password is correctly set

### Host Not Found
- Test DNS resolution: `nslookup halob`
- Use IP address instead: `192.168.86.31`
- Add host entry if needed: `echo "192.168.86.31 halob" >> /etc/hosts`

## Next Steps

1. Apply the PostgreSQL configuration changes on halob
2. Create the `antilurk` database and `antilurk_bot` user
3. Test connectivity from external machines
4. Update bot deployment configuration with the new DATABASE_URL