# Deployment Guide

This directory contains deployment configurations for the Telegram Anti-Lurk Bot.

## Quick Start with Docker Compose

1. **Copy environment configuration:**
   ```bash
   cp ../.env.example .env
   # Edit .env with your actual values
   ```

2. **Deploy with all services:**
   ```bash
   docker-compose up -d
   ```

3. **Deploy with minimal services (bot + database only):**
   ```bash
   docker-compose up -d telegram-antilurk-bot postgres
   ```

4. **Enable optional services:**
   ```bash
   # With NATS event publishing
   docker-compose --profile nats up -d

   # With PgAdmin database administration
   docker-compose --profile with-pgadmin up -d
   ```

## Portainer Stack Deployment

For deployment on NAS or server with Portainer:

1. **Copy the Portainer stack file:**
   - Use `portainer-stack.yml` in Portainer's stack creation interface

2. **Configure environment variables in Portainer:**
   ```env
   TELEGRAM_TOKEN=your_bot_token_here
   POSTGRES_PASSWORD=your_secure_database_password
   POSTGRES_USER=antilurk
   POSTGRES_DB=antilurk
   TZ=UTC
   ```

3. **Optional services with profiles:**
   - Add `COMPOSE_PROFILES=with-nats` for NATS event publishing
   - Add `COMPOSE_PROFILES=with-pgadmin` for database administration
   - Multiple profiles: `COMPOSE_PROFILES=with-nats,with-pgadmin`

## Service Configuration

### Core Services

#### telegram-antilurk-bot
- **Purpose**: Main bot application
- **Dependencies**: PostgreSQL database
- **Health Check**: Simple Python import test
- **Restart Policy**: Always restart unless stopped manually
- **Data Persistence**:
  - Bot configuration: `/data/config` volume
  - Application data: `/data` volume

#### postgres
- **Purpose**: Database for user tracking and message archiving
- **Image**: PostgreSQL 16 Alpine
- **Data Persistence**: `postgres_data` volume
- **Health Check**: PostgreSQL ready check
- **Port**: 5432 (configurable with `POSTGRES_PORT`)

### Optional Services

#### nats (Profile: `nats` or `with-nats`)
- **Purpose**: Event publishing for external integrations
- **Features**: JetStream persistence enabled
- **Ports**:
  - 4222 (NATS client port)
  - 8222 (HTTP management interface)
- **Data Persistence**: `nats_data` volume for JetStream
- **Configuration**:
  - 1GB max file store
  - 256MB max memory store

#### pgadmin (Profile: `with-pgadmin`)
- **Purpose**: Web-based PostgreSQL administration
- **Port**: 8080 (configurable with `PGADMIN_PORT`)
- **Access**: http://localhost:8080
- **Default Login**: Configure via `PGADMIN_EMAIL` and `PGLADMIN_PASSWORD`
- **Data Persistence**: `pgadmin_data` volume

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather | `123456789:ABCdefGhI...` |
| `POSTGRES_PASSWORD` | Database password | `secure_password_123` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `antilurk` |
| `POSTGRES_DB` | Database name | `antilurk` |
| `TZ` | Timezone for logs | `UTC` |
| `NATS_URL` | NATS server URL | `nats://nats:4222` |
| `NATS_SUBJECT_PREFIX` | NATS subject prefix | `antilurk` |
| `POSTGRES_PORT` | PostgreSQL external port | `5432` |
| `PGADMIN_PORT` | PgAdmin web interface port | `8080` |
| `PGADMIN_EMAIL` | PgAdmin login email | `admin@example.com` |
| `PGADMIN_PASSWORD` | PgAdmin login password | (required if using PgAdmin) |

## Volume Management

### Local Development
Volumes are managed by Docker Compose and persist data locally.

### Production/NAS Deployment
For production deployments, especially on NAS systems:

1. **Named volumes** (recommended for Portainer):
   ```yaml
   volumes:
     antilurk_bot_config:
       driver: local
   ```

2. **Host bind mounts** (for direct access to config files):
   ```yaml
   volumes:
     - /volume1/antilurk/config:/data/config
     - /volume1/antilurk/data:/data
   ```

## Health Checks and Monitoring

### Application Health
- **Bot health**: Simple Python import test every 30 seconds
- **Database health**: PostgreSQL ready check every 15 seconds
- **NATS health**: TCP connection check to port 4222

### Logging
- **Bot logs**: Structured JSON logs to stdout/stderr
- **Log levels**: Configure via `LOG_LEVEL` environment variable
- **Log rotation**: Handled by Docker logging driver

### Monitoring Integration
The bot publishes events to NATS for external monitoring:
- User activity events
- Challenge creation and responses
- System startup and shutdown events
- Configuration changes

## Backup and Recovery

### Database Backup
```bash
# Create backup
docker exec telegram-antilurk-postgres pg_dump -U antilurk antilurk > backup.sql

# Restore backup
docker exec -i telegram-antilurk-postgres psql -U antilurk antilurk < backup.sql
```

### Configuration Backup
```bash
# Backup configuration directory
docker cp telegram-antilurk-bot:/data/config ./config_backup
```

## Troubleshooting

### Common Issues

1. **Bot won't start - Token error**
   ```
   Solution: Verify TELEGRAM_TOKEN in .env file
   Test: Try the token with curl to Telegram API
   ```

2. **Database connection failed**
   ```
   Solution: Check DATABASE_URL format and credentials
   Test: Use docker exec to connect to postgres container
   ```

3. **Permission denied on config directory**
   ```
   Solution: Ensure volume permissions allow container write access
   Fix: chown -R 1000:1000 /volume1/antilurk/config
   ```

4. **Bot joins chats but commands don't work**
   ```
   Solution: Ensure bot has admin permissions in both chats
   Check: /antlurk help should list available commands
   ```

### Log Analysis
```bash
# View bot logs
docker logs telegram-antilurk-bot -f

# View database logs
docker logs telegram-antilurk-postgres -f

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Security Considerations

### Token Security
- Never commit `.env` files with real tokens
- Use Docker secrets in production if available
- Rotate tokens periodically

### Network Security
- Bot communicates only with Telegram API (outbound HTTPS)
- Database port should not be exposed externally in production
- Use internal Docker networks for inter-service communication

### Data Privacy
- Message content is stored for activity tracking
- Configure log retention policies
- Consider GDPR compliance for user data

## Updates and Maintenance

### Updating the Bot
```bash
# Pull latest image
docker-compose pull telegram-antilurk-bot

# Restart with new image
docker-compose up -d telegram-antilurk-bot
```

### Configuration Updates
1. Edit YAML files in the config volume
2. Use `/antlurk reboot` command to reload configuration
3. Or restart the container: `docker-compose restart telegram-antilurk-bot`

### Database Maintenance
- Database migrations are handled automatically on startup
- Consider periodic VACUUM and ANALYZE operations
- Monitor disk usage and configure log rotation