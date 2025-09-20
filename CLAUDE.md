# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram anti-lurk moderation bot designed for large communities. It identifies inactive members ("lurkers"), challenges them with simple puzzles in the moderated chat, and reports failures to a modlog channel for manual admin action. No automatic removal in v1.

## Key Architecture & Concepts

### Operating Model
- **Two chat types**: `moderated` (monitored for activity) and `modlog` (receives admin notifications)
- **Linking**: Many moderated chats can link to one modlog via forward-code handshake
- **No auto-kick**: Bot only notifies admins who manually kick users via Telegram admin tools

### Configuration System
- **Location**: `$CONFIG_DIR` (defaults to `/data/config` in container)
- **Files**:
  - `config.yaml`: Global defaults (thresholds, intervals, rate limits)
  - `channels.yaml`: Chat links and per-chat overrides
  - `puzzles.yaml`: Bank of challenge questions (~50 seeded on first run)
- **Checksum tracking**: Bot validates and adopts configs on startup; warns on manual edit overwrites
- **Precedence**: per-chat overrides > global defaults > built-in defaults

### Database Architecture
- **PostgreSQL** via `DATABASE_URL` environment variable
- **Core tables**:
  - `users`: User tracking with last interaction timestamps
  - `message_archive`: Full message history from moderated chats
  - `provocations`: Challenge session tracking
- **View**: `user_channel_activity` - aggregated per-user/per-chat statistics

### Key Defaults
- **Lurk threshold**: 14 days
- **Provocation interval**: 48 hours
- **Audit cadence**: 15 minutes
- **Rate limits**: 2 provocations/hour, 15/day per moderated chat

## Development Commands

### Project Setup
Since this is a specification/planning project without implementation yet:
```bash
# View project structure
ls -la

# Review specifications
cat specs/001-lurker-kicking-bot/spec.md
cat specs/001-lurker-kicking-bot/plan.md
cat specs/001-lurker-kicking-bot/tasks.md
```

### When Implementation Begins
The project will use:
- Python with `uv` for package management (per README)
- Docker for containerization
- PostgreSQL for persistence
- Telegram Bot API via token

Expected structure when implemented:
- Source code likely in `src/` directory
- Database migrations for schema setup
- Docker/Portainer deployment configuration in `deploy/`

## Bot Commands Reference

All commands use `/antlurk` root with subcommands:

### Mode & Linking
- `/antlurk mode [moderated|modlog]` - Set chat operating mode
- `/antlurk help` - List available commands and roles

### Admin Commands (moderated chat only)
- `/antlurk report active|inactive|lurkers [--days N] [--limit M]` - Activity reports
- `/antlurk checkuser <username|user_id>` - User activity lookup
- `/antlurk show reports [limit]` - Recent moderation activity

### System Commands
- `/antlurk show config` - Display effective configuration
- `/antlurk show links` - List chat linkages
- `/antlurk unlink <chat>` - Remove chat link
- `/antlurk reboot` - Graceful restart (exits with code 0)

## Environment Variables

Required:
- `TELEGRAM_TOKEN`: Bot token from @BotFather
- `DATABASE_URL`: PostgreSQL connection string

Optional:
- `DATA_DIR`: Base directory (default `/data`)
- `CONFIG_DIR`: Config directory (default `$DATA_DIR/config`)
- `TZ`: Timezone for display (default UTC)
- `NATS_URL`: Optional event publishing
- `NATS_SUBJECT_PREFIX`: NATS subject prefix (default `antilurk`)

## Implementation Status

Current state: **Specification phase**
- Detailed functional requirements documented
- Database schema designed
- Implementation plan with 9 phases
- Granular task list for tracking

Next steps per plan:
1. Phase 1: Config & bootstrapping implementation
2. Phase 2: Database model & migrations
3. Phase 3: Telegram bot core functionality
4. Phase 4-9: Progressive feature implementation

## Working with Specs

The project uses a structured specification approach:
- `specs/001-lurker-kicking-bot/spec.md` - Functional requirements
- `specs/001-lurker-kicking-bot/plan.md` - Implementation phases
- `specs/001-lurker-kicking-bot/tasks.md` - Granular task checklist

When implementing:
1. Follow the phases in plan.md sequentially
2. Check off tasks in tasks.md as completed
3. Validate against acceptance scenarios in spec.md
4. Maintain provenance tracking in config files