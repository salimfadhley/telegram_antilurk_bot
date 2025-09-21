# Database Setup for Telegram Anti-Lurk Bot

This guide shows how to set up a PostgreSQL database for the Telegram Anti-Lurk Bot using the existing halob PostgreSQL server.

## Prerequisites

- PostgreSQL 16 server running on halob (192.168.86.31:5432)
- Access to create databases and users
- Network connectivity from your deployment environment to halob

## Database Setup

### 1. Connect to PostgreSQL

Connect to the halob PostgreSQL server as a superuser:

```bash
# From a machine with psql client
psql -h halob -U postgres -d postgres

# Or using Docker exec on halob
docker exec -it postgres-16 psql -U postgres
```

### 2. Create Database and User

```sql
-- Create database for the bot
CREATE DATABASE antilurk;

-- Create user for the bot
CREATE USER antilurk_bot WITH ENCRYPTED PASSWORD 'GenerateSecurePasswordHere123!';

-- Grant all privileges on database
GRANT ALL PRIVILEGES ON DATABASE antilurk TO antilurk_bot;

-- Make user owner of database
ALTER DATABASE antilurk OWNER TO antilurk_bot;

-- Connect to the new database
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

### 3. Verify Database Setup

```sql
-- Check database exists
\l antilurk

-- Check user permissions
\du antilurk_bot

-- Test connection as bot user
\q
psql -h halob -U antilurk_bot -d antilurk
```

### 4. Test Connection from External Machine

From your development/deployment machine:

```bash
# Test with psql client
psql "postgresql://antilurk_bot:YourPasswordHere@halob:5432/antilurk" -c "SELECT version();"

# Test with Python (using our bot's session module)
python3 -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://antilurk_bot:YourPasswordHere@halob:5432/antilurk'
from telegram_antilurk_bot.database.session import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()')).first()
    print('Connected successfully:', result[0])
"
```

## Environment Configuration

### Docker Compose (.env file)

```env
# Database connection for the bot
DATABASE_URL=postgresql://antilurk_bot:YourPasswordHere@halob:5432/antilurk

# Or using separate variables (for docker-compose)
POSTGRES_HOST=halob
POSTGRES_PORT=5432
POSTGRES_DB=antilurk
POSTGRES_USER=antilurk_bot
POSTGRES_PASSWORD=YourPasswordHere
```

### Portainer Stack Environment Variables

In your Portainer stack, set:

```yaml
environment:
  - DATABASE_URL=postgresql://antilurk_bot:YourPasswordHere@halob:5432/antilurk
  - TELEGRAM_TOKEN=your_bot_token_here
```

## Network Configuration

### For Docker Bridge Networks

If your bot container uses a bridge network and can't resolve "halob":

```yaml
# Option 1: Use IP address directly
environment:
  - DATABASE_URL=postgresql://antilurk_bot:YourPasswordHere@192.168.86.31:5432/antilurk

# Option 2: Add extra hosts mapping
extra_hosts:
  - "halob:192.168.86.31"
environment:
  - DATABASE_URL=postgresql://antilurk_bot:YourPasswordHere@halob:5432/antilurk
```

### For Host Network Mode

If your bot container uses host network mode:

```yaml
network_mode: host
environment:
  - DATABASE_URL=postgresql://antilurk_bot:YourPasswordHere@localhost:5432/antilurk
```

## Database Schema Migration

The bot will automatically create its schema on first startup. The expected tables are:

- `users` - User tracking and activity
- `message_archive` - Full message history from moderated chats
- `provocations` - Challenge session tracking
- `user_channel_activity` (view) - Aggregated per-user/per-chat statistics

## Security Considerations

1. **Strong Password**: Use a strong, unique password for the `antilurk_bot` user
2. **Network Security**: Ensure PostgreSQL port 5432 is only accessible from trusted networks
3. **Connection Encryption**: Consider enabling SSL if the bot runs outside the local network
4. **Regular Backups**: Include the `antilurk` database in your backup procedures

## Backup Procedures

### Manual Backup

```bash
# Backup the antilurk database
docker exec postgres-16 pg_dump -U postgres antilurk > antilurk_backup_$(date +%Y%m%d).sql

# Compressed backup
docker exec postgres-16 pg_dump -U postgres antilurk | gzip > antilurk_backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore from backup
docker exec -i postgres-16 psql -U postgres antilurk < antilurk_backup.sql

# Restore from compressed backup
gunzip -c antilurk_backup.sql.gz | docker exec -i postgres-16 psql -U postgres antilurk
```

## Troubleshooting

### Connection Issues

1. **Check PostgreSQL is running:**
   ```bash
   docker ps | grep postgres-16
   docker exec postgres-16 pg_isready
   ```

2. **Test network connectivity:**
   ```bash
   telnet halob 5432
   # or
   nc -zv halob 5432
   ```

3. **Verify user credentials:**
   ```bash
   psql -h halob -U antilurk_bot -d antilurk
   ```

### Permission Issues

```sql
-- If you get permission denied errors, reconnect as postgres and run:
\c antilurk
GRANT ALL ON SCHEMA public TO antilurk_bot;
GRANT ALL ON ALL TABLES IN SCHEMA public TO antilurk_bot;
```

### Performance Optimization

For production deployments, consider these PostgreSQL settings:

```sql
-- Connect as postgres user
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
SELECT pg_reload_conf();
```

## Integration Testing

Use the bot's integration tests to verify database connectivity:

```bash
# Set the DATABASE_URL and run tests
export DATABASE_URL="postgresql://antilurk_bot:YourPasswordHere@halob:5432/antilurk"
uv run pytest tests/integration/test_database_connection.py -v
```

This should show successful connection and basic database operations.