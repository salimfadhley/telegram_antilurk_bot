# Implementation Plan — 001 Lurker Kicking Bot

This plan outlines the phases to deliver the Telegram anti‑lurk bot (moderated/modlog model), aligned with the current spec. Testing methodology is Strict TDD using pytest, with Hypothesis used selectively where it adds value.

## Phase 1 — Config & Bootstrapping
- Define schemas for `$CONFIG_DIR/config.yaml`, `channels.yaml`, `puzzles.yaml`.
- Establish pytest baseline and folder structure (`tests/unit`, `tests/integration`, `tests/contract`). Add initial failing tests for config validation and checksum adoption.
- Seed docs structure in `docs/` with high‑level overview and config file references.
- Implement YAML load + schema validate; adopt valid configs by recomputing/writing checksums on startup; exit with clear errors on invalid files.
- Seed default templates on first run (including ~50 puzzles) if files are missing.
- Persist provenance: `updated_at`, `updated_by`, `checksum` in each config file.
- Implement command‑driven config changes that apply immediately and persist to `config.yaml`; detect on‑disk checksum mismatch and warn when overwriting manual edits.

## Phase 2 — Database Model & Migrations
- Tables: `users`, `message_archive`, `provocations` (+ indexes on chat_id, user_id, sent_at).
- View: `user_channel_activity` (per user/per chat aggregates: message_count, last_message_at, last_provocation_at).
- Migrations + bootstrap (idempotent on startup).
 - Tests (pytest): unit tests for schema/migration generation and basic CRUD; integration tests for view correctness on sample fixtures. Consider Hypothesis for aggregation edge cases.

## Phase 3 — Telegram Bot Core
- Env + startup: validate `TELEGRAM_TOKEN`, `DATABASE_URL`; connect DB; load configs; post “bot is live” to modlogs.
- Modes: `/antlurk mode` (buttons) and `/antlurk mode moderated|modlog` (direct set). `/start` also triggers the same welcome/mode-selection UI.
- Linking: forward‑code handshake (generate link message in moderated; forward to modlog; 10‑min TTL; auto‑delete; persist link to `channels.yaml`).
- Help: `/antlurk help` lists commands, roles, and where they apply.
 - Tests: unit tests for command parsing; integration tests for mode change flows (mocks/stubs for Telegram API).

## Phase 4 — Audit & Scheduling
- Scheduler: run every `audit_cadence_minutes` (default 15).
- Selection: identify lurkers per moderated chat (threshold days), skip anyone provoked within the current provocation interval; enforce rate limits (2/hour, 15/day per chat).
- Backlog: carry over eligible users to later cycles when limits cap out (quietly; optional future notification).
 - Tests: unit tests for selection and rate-limit logic; integration tests simulating multiple chats and users. Consider Hypothesis for rate‑limit/scheduler invariants.

## Phase 5 — Challenge Flow
- Compose and post plain public puzzle messages in moderated chats (mention user; inline buttons; English‑only; choices randomized).
- Record a `provocations` row for each challenge; persist callback data.
- Handle callbacks: update outcome (correct/incorrect), thank in moderated chat; on incorrect/no‑response (after interval), post notice in modlog with Kick + confirmation.
- Kicking: manual only. After confirmation, post instructions to kick via Telegram admin tools; log action (no auto‑remove).
 - Tests: unit tests for puzzle selection/shuffle and callback handling; integration tests for end‑to‑end challenge lifecycle with a fake Telegram client.

## Phase 6 — Message & Event Logging
- Ingest moderated chat messages into `message_archive` (full text + metadata); update `users. Consider Hypothesis for rate‑limit/scheduler invariants.last_interaction_at`.
- Persist provocation lifecycle timestamps; maintain provocation history for rate limiting and reports.
- Optional NATS: publish notable events if `NATS_URL` configured.
 - Tests: integration tests verifying DB rows and view updates as messages and provocations occur.

## Phase 7 — Admin Commands & Reports
- `/antlurk show links|config|reports [limit]` (reports only in moderated chats).
- `/antlurk unlink <chat>`; regenerate linking message.
- `/antlurk checkuser <username|user_id>` with per‑chat message counts and last timestamps.
- `/antlurk report active|inactive|lurkers [--days N] [--limit M]` (moderated chats only).
- `/antlurk reboot`: exit 0 after persisting state and posting shutdown notice.
 - Tests: unit tests for command handlers; integration tests for permission and chat‑scoping rules.

## Phase 8 — Deployment & Ops
- Docker/Portainer stack; `.env.example`; README usage.
- Startup/shutdown notices to modlogs; logs to stdout/stderr.
 - Tests: basic smoke tests for containerized run (if CI permits), otherwise document manual validation steps.

## Phase 9 — Validation
- Dry‑run in a test group/modlog pair: linking, audit, challenges, callbacks, rate limits.
- Verify DB contents and `user_channel_activity` view; sanity‑check reports/checkuser.

## Notes
- Defaults: threshold 14 days; provocation interval 48h; cadence 15m; rate limits 2/hour & 15/day per chat.
- Config precedence: per‑chat overrides in `channels.yaml` > global in `config.yaml` > built‑ins.
- Search/announcements are de‑scoped for v1 (data collected for future indexing).
 - Test Framework: pytest for all test types; maintain tests under `tests/unit`, `tests/integration`, and `tests/contract`.
- Property‑based tests: Hypothesis used selectively for critical logic.
- Docs: Maintain hierarchical Markdown under `docs/` and update alongside features.
- Typing: Prefer adding stubs over ignores; include `py.typed` and local stubs to improve mypy signal.
