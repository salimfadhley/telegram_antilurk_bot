# Tasks — 001 Lurker Kicking Bot

This is a granular task list derived from the implementation plan. Use it to track progress and verify acceptance.

## Phase 1 — Config & Bootstrapping
- [x] Define YAML schemas (Python) for:
  - [x] `$CONFIG_DIR/config.yaml` (threshold, interval, cadence, rate limits, notices, features, provenance).
  - [x] `$CONFIG_DIR/channels.yaml` (chat entries, mode, modlog_ref, overrides, provenance).
  - [x] `$CONFIG_DIR/puzzles.yaml` (id, type, question, choices, correct_index, provenance).
- [x] Implement config loader:
  - [x] Load all three configs; validate against schema.
  - [x] On valid: recompute checksum, set `updated_at`, preserve `updated_by` if present, write back.
  - [x] On invalid: raise a structured error naming file and issues; exit non‑zero.
- [x] First‑run seeding:
  - [x] If missing, write default `config.yaml` (built‑in defaults), `channels.yaml` (empty chats list), and `puzzles.yaml` (~50 items).
- [x] Command‑driven config updates:
  - [x] Persist changes to `config.yaml` immediately.
  - [x] Before write: verify on‑disk checksum; if mismatch, still write and emit warning to modlog + invoking chat (include old/new checksums).
  - [x] Reconfigure schedulers/limits in memory after successful write.

## Phase 2 — Database Model & Migrations
- [x] Create migrations for tables:
  - [x] `users` (user_id, username, first_seen, last_seen, last_interaction_at, flags/roles).
  - [x] `message_archive` (chat_id, user_id, message_id, text, sent_at, edited_at, type, reply_to_id, forward_info, attachments, metadata JSON; indexes on (chat_id, user_id, sent_at)).
  - [x] `provocations` (provocation_id, chat_id, user_id, created_at, scheduled_at, sent_at, responded_at, outcome enum, puzzle_id, callback_data).
- [x] Create view `user_channel_activity`:
  - [x] Aggregates per (chat_id, user_id): message_count, last_message_at, last_provocation_at.
- [x] Bootstrap DB on startup (idempotent): apply migrations if needed.

## Phase 3 — Telegram Bot Core
- [x] Startup checks: `TELEGRAM_TOKEN`, `DATABASE_URL`, `CONFIG_DIR` writable; connect DB.
- [x] Post "bot is live" notice to all configured modlog chats.
- [x] Implement `/antlurk help` (commands, roles, where usable).
- [x] Implement `/antlurk mode`:
  - [x] No args: show inline buttons (moderated/modlog).
  - [x] With arg: set mode immediately; persist to `channels.yaml`.

## Phase 4 — Linking (Forward‑Code Handshake)
- [ ] In moderated chat, generate linking message with unique code (10‑min TTL) when mode set and no link exists.
- [ ] Detect forwarded linking message in modlog chat; validate code, presence in both chats, admin rights.
- [ ] Persist link (moderated→modlog) to `channels.yaml`; confirm in both chats; delete original linking message (on use/expiry).

## Phase 5 — Audit & Scheduling
- [ ] Scheduler loop at `audit_cadence_minutes` (default 15): per moderated chat
  - [ ] Identify lurkers (last interaction > lurk_threshold_days).
  - [ ] Exclude users provoked within current `provocation_interval_hours`.
  - [ ] Enforce rate limits: ≤2/hour, ≤15/day per chat (configurable); backlog remainder.
  - [ ] Queue challenges accordingly.

## Phase 6 — Challenge Flow
- [ ] Compose puzzle from `puzzles.yaml`; randomize choices; mention user.
- [ ] Post plain public challenge message with inline buttons in moderated chat.
- [ ] Insert `provocations` row (created_at, scheduled_at/sent_at, puzzle_id, callback data).
- [ ] Handle callbacks:
  - [ ] Correct: thank user in moderated chat; update outcome.
  - [ ] Incorrect: thank user with nudge; post modlog notice with Kick + confirmation; update outcome.
  - [ ] Timeout (on interval expiry): post modlog notice with Kick + confirmation.
- [ ] Kick flow: confirmation → post instructions for manual removal; do not auto‑kick; log action.

## Phase 7 — Message & Event Logging
- [ ] Ingest moderated chat messages to `message_archive` (full text + metadata).
- [ ] Update `users` table and `last_interaction_at`.
- [ ] Optional: publish events to NATS if `NATS_URL` is set.

## Phase 8 — Admin Commands & Reports
- [ ] `/antlurk show links` (list moderated→modlog mappings) — allowed in both chats.
- [ ] `/antlurk show config` (current effective values; indicate override sources) — both chats.
- [ ] `/antlurk show reports [limit]` — only moderated chats; internal logs when no modlog linked.
- [ ] `/antlurk unlink <chat>` — admin‑only; remove link; confirm.
- [ ] `/antlurk checkuser <username|user_id>` — in moderated chat; show per‑chat message counts and last timestamps, lurk status, provocation stats.
- [ ] `/antlurk report active|inactive|lurkers [--days N] [--limit M]` — only moderated chats.
- [ ] `/antlurk reboot` — post shutdown notice; persist state; exit 0.

## Phase 9 — Deployment & Ops
- [ ] Provide Portainer stack (deploy/portainer-stack.yaml) + `.env.example`.
- [ ] README: envs, Portainer mapping, config edit/reboot flow, checksum warnings, limits behavior.
- [ ] Post “shutting down” notice on termination for all modlog chats.

## Acceptance Checklist
- [ ] Valid configs are adopted on startup; invalid ones cause clear crash messages.
- [ ] Linking works: code TTL, admin checks, persistence, deletion on use/expiry.
- [ ] Scheduler respects threshold, interval, rate limits; no re‑provocation within interval.
- [ ] Challenges appear as public messages; buttons work; outcomes logged; modlog notices on incorrect/timeout.
- [ ] Kicks are manual‑only with confirmation and instructions (no auto‑remove).
- [ ] Message and provocation logs populate DB; `user_channel_activity` view returns expected aggregates.
- [ ] Admin commands function and enforce chat/role constraints.
- [ ] Startup/shutdown notices delivered to modlog chats.

