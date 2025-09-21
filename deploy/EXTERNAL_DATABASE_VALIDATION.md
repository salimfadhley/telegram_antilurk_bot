# External Database Connection Validation Guide

This document provides step-by-step instructions to validate that the Telegram Anti-Lurk Bot can successfully connect to the PostgreSQL database on halob from external machines.

## Prerequisites

- Network connectivity to halob (192.168.86.31)
- PostgreSQL server running on halob:5432
- `antilurk` database and user configured
- Bot project dependencies installed (`uv sync`)

## Quick Validation Commands

### 1. Test Network Connectivity

```bash
# Test hostname resolution
ping -c 1 halob

# Test PostgreSQL port accessibility
nc -zv halob 5432
# or using IP address
nc -zv 192.168.86.31 5432
```

Expected output:
```
halob.lan [192.168.86.31] 5432 (postgresql) open
```

### 2. Test PostgreSQL Connection with psql

```bash
# Test direct psql connection
psql postgresql://antilurk:antilurk@halob:5432/antilurk -c "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"
```

Expected output:
```
current_database | current_user | inet_server_addr | inet_server_port
------------------+--------------+------------------+------------------
 antilurk         | antilurk     | 192.168.86.31    |             5432
(1 row)
```

### 3. Test Python SQLAlchemy Integration

```bash
# Test with our custom validation script
DATABASE_URL="postgresql://antilurk:antilurk@halob:5432/antilurk" uv run python test_database_final.py
```

Expected output:
```
🔍 Testing Telegram Anti-Lurk Bot Database Integration
=======================================================
1. Testing get_engine() function...
   ✅ Engine created successfully
2. Testing database connection...
   ✅ Connected to database: antilurk
   ✅ Connected as user: antilurk
   ✅ PostgreSQL version: PostgreSQL 16.9 (Debian 16.9-1.pgdg120+1) on x86_6...
3. Testing basic operations...
   ✅ Basic math: 1 + 1 = 2
   ✅ Server time: 2025-09-21 01:11:29.759677+00:00
   ✅ Table operations: 1 row inserted
   ✅ Table cleanup successful
4. Testing network info...
   ✅ Server IP: 192.168.86.31
   ✅ Server port: 5432
   ✅ Listen addresses: *

🎉 SUCCESS: All database connectivity tests passed!
```

### 4. Test Bot Integration Tests

```bash
# Run bot's integration tests with external database
DATABASE_URL="postgresql://antilurk:antilurk@halob:5432/antilurk" uv run pytest tests/integration/test_database_connection.py::test_database_connect_and_simple_query -v
```

### 5. Test with Multiple Connection Scenarios

```bash
# Test comprehensive connectivity scenarios
DATABASE_URL="postgresql://antilurk:antilurk@halob:5432/antilurk" uv run python deploy/test_external_connection.py
```

## Connection String Formats

### Working Connection Strings

```bash
# Using hostname
DATABASE_URL="postgresql://antilurk:antilurk@halob:5432/antilurk"

# Using IP address
DATABASE_URL="postgresql://antilurk:antilurk@192.168.86.31:5432/antilurk"
```

### Docker Environment Variables

For docker-compose or Portainer:

```yaml
environment:
  - DATABASE_URL=postgresql://antilurk:antilurk@halob:5432/antilurk
  # Alternative format
  - POSTGRES_HOST=halob
  - POSTGRES_PORT=5432
  - POSTGRES_DB=antilurk
  - POSTGRES_USER=antilurk
  - POSTGRES_PASSWORD=antilurk
```

## Troubleshooting Common Issues

### Connection Refused

**Symptoms:**
```
connection to server at "halob" (192.168.86.31), port 5432 failed: could not connect to server: Connection refused
```

**Solutions:**
1. Check if PostgreSQL is running: `ssh sal@halob "docker ps | grep postgres-16"`
2. Verify port is accessible: `nc -zv halob 5432`
3. Check container logs: `ssh sal@halob "docker logs postgres-16 --tail 20"`

### Authentication Failed

**Symptoms:**
```
FATAL: password authentication failed for user "antilurk"
```

**Solutions:**
1. Verify user exists: `ssh sal@halob "docker exec postgres-16 psql -U postgres -c '\\du antilurk'"`
2. Reset password: `ssh sal@halob "docker exec postgres-16 psql -U postgres -c \"ALTER USER antilurk WITH PASSWORD 'antilurk';\"`
3. Check pg_hba.conf allows external connections

### Database Does Not Exist

**Symptoms:**
```
FATAL: database "antilurk" does not exist
```

**Solutions:**
1. Check database exists: `ssh sal@halob "docker exec postgres-16 psql -U postgres -l | grep antilurk"`
2. Create database: `ssh sal@halob "docker exec postgres-16 psql -U postgres -c 'CREATE DATABASE antilurk;'"`

### Name Resolution Failed

**Symptoms:**
```
could not translate host name "halob" to address: Name or service not known
```

**Solutions:**
1. Use IP address instead: `192.168.86.31`
2. Add to /etc/hosts: `echo "192.168.86.31 halob" | sudo tee -a /etc/hosts`
3. Test with ping: `ping halob`

## Validation Checklist

Use this checklist to verify external database connectivity:

- [ ] **Network Layer**
  - [ ] Can ping halob hostname
  - [ ] Can reach port 5432 (nc -zv test)
  - [ ] Hostname resolves to 192.168.86.31

- [ ] **Database Layer**
  - [ ] PostgreSQL container is running on halob
  - [ ] antilurk database exists
  - [ ] antilurk user exists with proper permissions
  - [ ] Can connect with psql from external machine

- [ ] **Application Layer**
  - [ ] Python can import database session module
  - [ ] SQLAlchemy engine creation works
  - [ ] Can execute basic queries
  - [ ] Can create/drop tables (permissions test)
  - [ ] Bot integration tests pass

- [ ] **Security Layer**
  - [ ] Connection uses encrypted password authentication
  - [ ] User has minimal required permissions
  - [ ] Connection is limited to antilurk database only

## Environment Setup for Development

Add to your shell profile (~/.bashrc, ~/.zshrc):

```bash
# Telegram Anti-Lurk Bot Database
export DATABASE_URL="postgresql://antilurk:antilurk@halob:5432/antilurk"
```

Or create a .env file in the project root:

```env
DATABASE_URL=postgresql://antilurk:antilurk@halob:5432/antilurk
```

## Production Deployment

For production deployments, ensure:

1. **Strong Password**: Change from 'antilurk' to a secure password
2. **Environment Variables**: Use secrets management for DATABASE_URL
3. **Network Security**: Limit access to required IP ranges
4. **SSL/TLS**: Consider enabling SSL for encrypted connections
5. **Monitoring**: Set up connection monitoring and alerting

Example production connection string:
```bash
DATABASE_URL="postgresql://antilurk_bot:$(cat /run/secrets/db_password)@halob:5432/antilurk?sslmode=require"
```

## Success Indicators

A successful validation should show:

1. **Network connectivity**: Port 5432 accessible
2. **Database authentication**: User can log in
3. **Permissions**: Can create/drop tables in antilurk database
4. **Python integration**: SQLAlchemy engine works
5. **External access**: Connection works from development machine
6. **Server info**: Shows correct server IP (192.168.86.31)

## Next Steps

Once validation passes:

1. Update bot configuration with DATABASE_URL
2. Run database migrations (when implemented)
3. Deploy bot with external database connection
4. Set up monitoring for database connectivity
5. Configure backup procedures for antilurk database