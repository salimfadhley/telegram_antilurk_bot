# Telegram Anti‑Lurk Bot

A moderation helper for large Telegram communities. It identifies lurkers (inactive members), posts simple multiple‑choice “are you still here?” challenges in the moderated chat, and reports failures/timeouts to a linked modlog chat with an admin‑only Kick button. No automatic removals in v1.

## Quick Start (Docker / Portainer)

- Mount a host directory to `/data` in the container (default `DATA_DIR`). For Portainer on a NAS, a common path is `/volume1/telegram_antilurk_bot/data` → `/data`.
- Provide required environment variables:
  - `TELEGRAM_TOKEN`: Telegram bot token (from BotFather).
  - `DATABASE_URL`: PostgreSQL connection string.
  - `DATA_DIR` (optional): Defaults to `/data`.
  - `CONFIG_DIR` (optional): Defaults to `$DATA_DIR/config`.
  - `TZ` (optional): Timezone for human‑readable timestamps.

Example docker‑compose (Portainer Stack):

```
version: "3.9"
services:
  telegram_antilurk_bot:
    image: ghcr.io/your-org/telegram-antilurk-bot:latest
    container_name: telegram_antilurk_bot
    env_file: .env
    environment:
      - DATA_DIR=/data
      - CONFIG_DIR=/data/config
      - TZ=UTC
      # Optional NATS integration for event publishing
      # - NATS_URL=nats://nats:4222
      # - NATS_SUBJECT_PREFIX=antilurk
    volumes:
      - /volume1/telegram_antilurk_bot/data:/data
    restart: unless-stopped
```

`.env` file (create from `.env.example`):

```
TELEGRAM_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVwxyZ-1234567890
DATABASE_URL=postgres://user:password@db-host:5432/antilurk
# Optional overrides
DATA_DIR=/data
CONFIG_DIR=/data/config
TZ=UTC
# Optional integrations
# NATS_URL=nats://nats:4222
# NATS_SUBJECT_PREFIX=antilurk
```

On first run, invite the bot to:
- One moderated chat (the channel you want to manage)
- One modlog chat (where moderation notices appear)

Then:
- In each chat, set mode with `/antlurk mode moderated` or `/antlurk mode modlog`.
- In the moderated chat, if not yet linked, the bot will generate a linking message with a code. Forward that exact message to the modlog chat to complete the link (10‑minute TTL; auto‑deletes when used/expired).

## Environment Variables

- `TELEGRAM_TOKEN` (required): Telegram Bot API token.
  - How to get it: In Telegram, start a chat with `@BotFather` → `/newbot` → follow prompts. BotFather returns a token similar to `123456789:AAE2Zx…`.
  - Keep it secret; treat like a password.
- `DATABASE_URL` (required): PostgreSQL connection string.
  - Formats supported: `postgres://user:pass@host:port/dbname` or `postgresql://user:pass@host:port/dbname`
  - Example: `postgres://antilurk:changeme@postgres:5432/antilurk`
- `DATA_DIR` (optional): Base data directory. Defaults to `/data`.
- `CONFIG_DIR` (optional): Directory for YAML configs. Defaults to `$DATA_DIR/config`.
  - Files used:
    - `channels.yaml`: Links moderated chats → modlog chat; per‑chat overrides.
    - `config.yaml`: Global defaults (lurk threshold, provocation interval, audit cadence, rate limits).
    - `puzzles.yaml`: Bank of simple multiple‑choice puzzles. Seeded with ~50 on first run if missing.
  - `NATS_URL` (optional): If set, the bot may publish events/logs to NATS.
  - `NATS_SUBJECT_PREFIX` (optional): Subject prefix for NATS messages (e.g., `antilurk`).
- `TZ` (optional): e.g., `Europe/London`. If unset, UTC is used.

## Fail‑Fast Behavior (required)

On startup the bot validates critical configuration and will exit with a clear, actionable message if something is missing/misconfigured:
- Missing `TELEGRAM_TOKEN` → “Missing TELEGRAM_TOKEN. Create a bot via @BotFather and set TELEGRAM_TOKEN. See README.md.”
- Missing `DATABASE_URL` → “Missing DATABASE_URL. Provide a Postgres URL like postgres://user:pass@host:5432/dbname.”
- Database unreachable → “Cannot connect to PostgreSQL at DATABASE_URL. Check credentials/network and try again.”
- `CONFIG_DIR` not writable → “CONFIG_DIR ‘/data/config’ not writable. Mount a volume and correct permissions.”
- Invalid config file(s) → The bot names the invalid file(s) (`config.yaml`,
  `channels.yaml`, `puzzles.yaml`) and the specific problems (missing keys,
  wrong types, invalid values), then exits non‑zero. For valid files, the bot
  recomputes and writes checksums (“adopts” current content) on startup.

## Moderator Workflow (Summary)

- Set chat modes: `/antlurk mode moderated` in moderated chats; `/antlurk mode modlog` in modlog chat. `/antlurk mode` (no args) shows inline buttons to switch.
- Link chats: In moderated chat, the bot posts a linking message; forward it to the modlog chat to link (many moderated → one modlog supported).
- Audit & challenge: Audit runs every 15 minutes; you can also trigger manually from the moderated chat. Bot posts multiple‑choice puzzles mentioning lurkers. Challenges respect rate limits (default 2/hour, 15/day per moderated chat).
- Reboot: `/antlurk reboot` cleanly exits the process with status 0; your container orchestrator should restart the container.
 - Check user: `/antlurk checkuser <username|user_id>` returns per‑moderated‑chat activity and status.
 - Config changes: Edit `$CONFIG_DIR/config.yaml` (cadence, provocation interval, rate limits) and run `/antlurk reboot` to apply. On startup/shutdown the bot posts a notice to all linked modlog chats.
  - Safety: When applying config changes via commands, the bot verifies the on‑disk config checksum. If it has changed (manual edit), it applies your change but warns that it overwrote a manual edit (shows old/new checksums). Use `/antlurk reboot` after manual edits to reload cleanly.

## Development

- Python build tool: `uv` is recommended for local development and packaging.
- For native testing (outside Docker), set env vars (`DATA_DIR`, `CONFIG_DIR`, `TELEGRAM_TOKEN`, `DATABASE_URL`) in your shell.
- Pre-commit hooks: install and enable
  - pipx install pre-commit (or `uvx pre-commit` on demand)
  - pre-commit install && pre-commit install -t commit-msg
  - Hooks use `uvx` to run tools (ruff, mypy, pytest, bandit, yamllint, commitizen). No hygiene checks included.
- Responses:
  - Any button press resets the user’s last‑interaction.
  - Correct answer → Thank user; no modlog post.
  - Wrong or no answer (after 48h) → Modlog post with Kick button.
- Reports (moderated chat only): `/antlurk report active|inactive|lurkers` with optional `--days` and `--limit`.
 - Lookup: `/antlurk checkuser <username|user_id>` in a moderated chat returns
   last interaction, current lurk status, provocation count, last challenge
   status, and per‑moderated‑chat message counts with the most recent message
   timestamp per chat.
 - Help: `/antlurk help` lists available commands, roles, and where to use them.

## Data & Persistence

- PostgreSQL is the system of record (messages, challenge sessions, schedules).
- YAML in `CONFIG_DIR` is for static configuration only (links and defaults).
- Default thresholds: lurk 14 days; provocation interval 48h (overridable by YAML per‑chat or global defaults).
 - Core tables (simplified):
   - `users`: one row per encountered user; tracks last interaction.
  - `message_archive`: one row per message in moderated chats (full text + metadata).
   - `provocations`: one row per provocation initiated (timestamps, outcome).
   - View `user_channel_activity`: per chat/user — message_count, last_message_at, last_provocation_at.

## Security Notes

- Restrict admin commands to chat admins only (both moderated and modlog chats).
- Do not share tokens or database credentials in screenshots/logs.

## License

See repository for license information.
