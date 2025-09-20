# Feature Specification: Lurker Kicking Bot

**Feature Branch**: `[001-lurker-kicking-bot]`  
**Created**: 2025-09-20  
**Status**: Draft  
**Input**: User description: "lurker-kicking-bot"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## Background

This bot supports moderation for a large Telegram community associated with a
popular YouTube channel. Its core goal is to identify and ultimately reduce the
number of non‑participating members ("lurkers") to maintain an engaged
community. A member is considered a lurker when they have not responded within
the configured "lurk threshold" — 14 days by default (configurable). The
system tracks the last time a member responded and uses public challenges in the
moderated chat to gauge engagement before any manual moderation action by admins.
For v1, the bot does not remove users automatically; it informs admins via a
modlog channel or, if unlinked, retains internal reports accessible from the
moderated channel.

## Roles

- Moderator/Admin/Mod: Interacts with the bot to operate moderation features
  (typically from the modlog chat).
- Operator/Sysadmin: Installs and configures the bot (Docker/Portainer, DB,
  YAML configs).
- User/Channel member: Non‑privileged member who may be challenged as a lurker.

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As the Telegram group owner/mod, I want a bot to audit the group for inactive
lurkers, challenge them in the moderated chat with a simple multiple‑choice
puzzle (arithmetic or common‑sense) to confirm they are human/active, and
publish outcome reports to a linked modlog channel (no auto‑removal), so the
community stays engaged and admins stay informed.

### Acceptance Scenarios
1. Given a group with 1000 members and an inactivity threshold of 14 days
   (default, configurable), when an admin runs the audit command, then the
   bot posts a public challenge in the moderated chat with a simple
   multiple‑choice puzzle (mentioning the user) and
   records a ChallengeSession for each.
2. Given a challenged user does not respond within the provocation interval
   (default 48h, configurable), when the interval expires, then the bot posts
   a notification to the configured modlog channel stating the user did not
   respond and schedules the next prompt cycle (no maximum), incrementing the
   per-user prompt count.
   If the user responds at any time by pressing an answer button in the
   moderated chat, then the bot
   resets their last‑interaction timestamp. If the answer is correct, the bot
   thanks them; if the answer is incorrect, the bot thanks them and posts to
   the modlog channel that they failed the challenge with an inline Kick
   button.
3. Given a user selects an incorrect answer, when the bot processes the
   response, then it logs the failure, thanks the user with a light nudge
   (e.g., “are you sure about that?”), and posts to the modlog channel with a
   Kick button for admins to act.
4. Given a channel is configured in moderated mode and linked to a modlog
   channel, when messages are posted in the moderated channel, then the bot
   archives message metadata/content digests for search and analytics and
   publishes audit summaries and outcomes to the modlog channel.
5. Given a user is an admin in either the moderated channel or the modlog
   channel, when they issue an admin command to the bot, then the command is
   accepted and executed; if a non‑admin issues a command, the bot rejects it
   and optionally informs them they lack permission.
6. Given the bot is invited to a new Telegram chat, when it joins, then it
   posts a welcome message with inline buttons to select a mode (`moderated` or
   `modlog`) and also mentions the root command `/antlurk mode <moderated|modlog>`;
   if no selection is made, it defaults to `moderated`.
7. Given an admin sets a chat to `moderated` mode and no modlog link exists,
   when the admin runs `/antlurk mode moderated`, then the bot generates and
   posts a linking message in that chat (containing a unique code) instructing
   admins to forward it to their modlog channel to establish the link. This is
   the message that must be forwarded for linking.
8. Given that linking message is forwarded to a modlog channel where the bot is
   present, when the bot detects a valid, unexpired code, then it links the
   source moderated chat to the destination modlog channel and confirms in
   both places, and deletes the original linking message. If the code is
   invalid or expired (10‑minute TTL), the bot deletes the stale message and
   asks to retry by issuing a new link message.
9. Given multiple moderated channels are linked to one modlog channel,
   when reports are emitted, then the modlog messages indicate the source
   channel name/ID to disambiguate.
10. Given no modlog channel has been linked for a moderated channel, when
    the bot generates reports or outcomes, then it records them internally and
    makes them available via admin queries issued in the moderated channel
    only, until a modlog is linked.
11. Given an admin attempts to view reports outside a moderated channel (e.g.,
    in a modlog channel), when they run `/antlurk show reports`, then
    the bot rejects the request and states that reports are only displayed in
    moderated channels.
12. Given an admin runs `/antlurk mode` without arguments in either a moderated
    or modlog chat, when the bot receives the command, then it displays the
    same inline mode selection buttons so the admin can quickly switch modes; if
    the admin runs `/antlurk mode moderated` or `/antlurk mode modlog`, the bot
    switches immediately without showing the button.
12. Given an admin wants activity insights, when they run
    `/antlurk report active [--days 7|30|N] [--limit M]` in a moderated
    channel, then the bot returns the most active users within the time window,
    ordered by message count.
13. Given an admin wants to identify low activity, when they run
    `/antlurk report inactive [--days N] [--limit M]` in a moderated channel,
    then the bot returns users with the fewest messages in the window (excluding
    non‑members, bots, and allowlisted roles).
14. Given an admin wants to list lurkers, when they run
    `/antlurk report lurkers [--threshold-days D] [--limit M]` in a moderated
    channel, then the bot returns users whose last response exceeds the lurk
    threshold (default 14 days), including last activity timestamps.
15. Given the system operates across multiple chats, when additional moderated
    or modlog chats are added, then each chat can be configured independently;
    at minimum, one moderated chat and one modlog chat are required for full
    operation, but more than one of each type is supported.
16. Given provocation scheduling is active, when the bot selects lurkers to
    challenge, then it enforces rate limits: by default no more than 2
    provocations per hour and no more than 15 per day per moderated chat.
17. Given an admin taps the Kick button in the modlog chat, when the bot
    receives the request, then it asks for a confirmation (Yes/No). After
    confirmation, the bot does not perform automatic removal; instead it posts
    clear instructions for admins to manually remove the user via Telegram
    tools and logs the request.
18. Given an admin runs `/antlurk reboot`, when the bot receives the command,
    then it performs a graceful restart of internal components (reloads config,
    reschedules jobs) or exits to allow the container to restart, and reports
    status in the modlog chat.
19. Given an admin runs `/antlurk checkuser <username|user_id>` in a moderated
    chat, when the bot receives the command, then it returns a summary
    including: overall last interaction timestamp; current lurk status;
    provocation counts; last challenge status; and per‑moderated‑chat activity
    showing total message count and most recent message timestamp in each
    moderated chat the system manages.
20. Given the bot starts and `$CONFIG_DIR` is missing expected files, when
    initialization runs, then default templates for `channels.yaml`,
    `config.yaml`, and `puzzles.yaml` are created with sensible defaults and a
    starter bank of ~50 puzzles; operators can edit these later.
21. Given the bot starts up, when initialization completes, then it posts a
    “bot is live” message to each configured modlog chat. Given a shutdown or
    reboot is initiated, when the bot is terminating, then it posts a “bot
    shutting down” message to each configured modlog chat before exit.
22. Given a user was provoked recently, when the scheduler runs, then the bot
    MUST skip provoking that user again if the last provocation was within the
    current provocation interval, even if they still qualify as a lurker.
23. Given an admin changes a setting via an `/antlurk` command that persists to
    `config.yaml`, when the bot detects the on-disk checksum does not match the
    expected value (indicating a manual edit), then it still applies the change
    but posts a warning in the modlog (and to the invoking chat) that a manual
    change was overwritten, including old/new checksums and a reminder to use
    `/antlurk reboot` after manual edits.
24. Given the bot starts, when it loads `config.yaml`, `channels.yaml`, and
    `puzzles.yaml`, then it validates each against expected schema/constraints;
    if valid, it recomputes and writes checksums and adopts the configs. If any
    file is invalid, the bot exits with a clear error specifying which file and
    which keys/lines failed validation.
3. Given challenges are posted to a moderated chat, when the bot creates a
   challenge, then it posts a plain public message (not threaded) that mentions
   the target user and presents multiple-choice buttons in English.

### Edge Cases
 - Platform limits: respect Telegram rate limits with backoff.
 - Protections: admins/mods/allowlisted users are never removed.
 - Failure handling: network/API errors retried with jitter; actions idempotent.
 - Reactions or read receipts alone do not count as responses.
 - Platform constraint: Telegram does not support making a group message
   visible only to one user. Challenges are public in the moderated chat. The
   bot mentions the target user and uses inline buttons to capture responses.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: MUST identify lurkers using an inactivity threshold of 14 days
  by default (configurable) and recent activity heuristics for Telegram.
 - **FR-002**: MUST challenge identified lurkers in the moderated chat with a
   simple multiple‑choice puzzle (e.g., basic arithmetic or common‑sense
   questions such as “What colour is a fresh banana?”). MUST
   wait a provocation interval (default 48h, configurable) before re‑prompting.
   There is no maximum prompt cycle; MUST track and expose per‑user prompt
   counts.
- **FR-003**: MUST NOT auto‑remove users. On user response or timeout, MUST
  notify a configured modlog channel. If the user selects the wrong answer or
  does not respond within the provocation interval, the notification MUST
  include an inline Kick button for admins. MUST log a ModerationAction with
  timestamps.
 - **FR-004**: SHOULD post show announcements with a configurable template and
  lead time in a future version; de‑scoped for initial MVP unless configured.
- **FR-005**: MUST store group messages and rich metadata to support future
  indexing and analysis (search/reporting deferred). For v1, search UX is
  de‑scoped; data is collected now for future features.
- **FR-006**: MUST provide an admin-only user lookup interface via bot commands
  (search de-scoped for v1).
 - **FR-006a**: MUST provide a help command `/antlurk help` accessible in both
  moderated and modlog chats that lists available commands, required roles, and
  where each command can be used.
- **FR-007**: MUST support sending prompts and notifications at any time (no
  quiet hours) and provide a dry‑run mode for bulk operations.
- **FR-008**: MUST maintain audit logs of actions (challenge, acknowledge,
  notify, announce) and provide export on request.
 - **FR-009**: MUST support Telegram groups/venues in v1 (Discord is
   out‑of‑scope for this version).
- **FR-010**: MUST protect admins/mods/allowlisted users from automated
  prompts and negative flags.
 - **FR-016**: MUST support two channel operating modes per Telegram chat:
   `moderated` mode (the bot moderates and archives this channel) and `modlog`
   mode (the bot publishes reports and actions for admins).
 - **FR-017**: MUST allow linking one or more moderated channels to a modlog
   channel (many‑to‑one). If no modlog channel is configured, MUST still log
   internally and allow admins to query status via commands.
 - **FR-018**: MUST restrict admin commands to Telegram users who are admins in
   either the linked moderated channel(s) or the modlog channel. Non‑admins
   MUST be denied.
 - **FR-019**: MUST archive messages (metadata + content digests) in
   `moderated` mode channels to support search and activity heuristics.
 - **FR-020**: On being added to a chat, MUST prompt admins to choose a mode
   using inline buttons (`moderated` or `modlog`), and default to `moderated` if
   not set; MUST use a single root command `/antlurk` with subcommands,
   including `/antlurk mode <moderated|modlog>`. Running `/antlurk mode` with no
   arguments MUST display the inline mode selection buttons.
 - **FR-021**: MUST support link establishment via forward‑code handshake:
   when a moderated channel lacks a modlog link, the bot posts a message with
   instructions and a unique code; forwarding that exact message to a modlog
   channel where the bot is present completes the link. Codes MUST expire after
   10 minutes and be single‑use; bot MUST verify the forward and the caller's
   admin rights and MUST delete the link message upon use or expiry.
 - **FR-022**: MUST support introspection and admin utilities via the root
   command namespace, e.g., `/antlurk show links`, `/antlurk show config`,
   `/antlurk show reports [limit]`, `/antlurk unlink <chat>`. Commands MUST
   respect admin checks. `show reports` MUST only display in moderated
   channels; running it elsewhere results in a polite refusal. When no modlog
   is linked, `show reports` provides recent internal logs to admins in the
   moderated channel.
  - **FR-026**: MUST provide reporting subcommands under `/antlurk report` that
    only execute in moderated channels: `active`, `inactive`, `lurkers`, each
    with optional `--days` and `--limit` parameters and sensible defaults
    (default window 30 days; default limit 20).
  - **FR-027**: MUST compute activity based on message counts within the window
    and identify lurkers based on last valid response timestamp compared to the
    configured lurk threshold (default 14 days, channel‑overridable).
  - **FR-028**: MUST exclude admins/mods/allowlisted/bots from punitive lists
    (e.g., `inactive`, `lurkers`) while still allowing their activity to appear
    in `active` reports if desired [configurable].
  - **FR-029**: MUST return report results with usernames, user IDs, counts,
    and last activity timestamps; MUST support simple pagination via `--offset`
    or by emitting a “show more” control if supported.
  - **FR-030**: SHOULD ensure queries are efficient on PostgreSQL using
    appropriate indexes on message timestamp, chat ID, user ID, and message
    type; large channels should return reports within a reasonable time budget.
  - **FR-031**: MUST reset a member’s last‑interaction timestamp on any message
    they post in the moderated channel and on any challenge answer button press
    (correct or incorrect).
  - **FR-032**: The Kick button posted to the modlog channel MUST only be
    usable by admins; on confirmation, the bot MUST NOT perform automatic
    removal. Instead, it posts clear instructions to perform a manual kick via
    Telegram admin tools and logs the request in audit logs.
  - **FR-033**: Passing a challenge (correct answer) MUST NOT generate a modlog
    post; the outcome MUST still be recorded in audit logs and reflected in
    the member’s status.
  - **FR-039**: MUST enforce provocation rate limits per moderated chat: default
    maximum 2 provocations per hour and 15 per day; values are configurable via
    `$CONFIG_DIR/config.yaml` and per‑chat overrides in `channels.yaml`.
  - **FR-040**: The Kick action MUST require a confirmation step (e.g., inline
    Yes/No). Only confirmed actions by admins proceed to attempt removal.
  - **FR-041**: MUST support `/antlurk reboot` for admins by terminating the
    process with exit code 0 after logging intent. Rely on the container runner
    (e.g., Docker/compose/Portainer) to restart the container. Ensure any
    in-memory schedules/state are persisted before exit.
  - **FR-042**: MUST support `/antlurk checkuser <username|user_id>` for admins
    in a moderated chat, returning: overall last interaction timestamp; current
    lurk status; provocation count; last challenge status; and per‑moderated‑chat
    activity (message count and most recent message timestamp per moderated chat).
    If the user is unknown or not a member, respond clearly.
  - **FR-035**: MUST read the Telegram bot token from `TELEGRAM_TOKEN` at
    startup; fail fast with a clear error if missing.
  - **FR-036**: MUST read PostgreSQL connection configuration from
    `DATABASE_URL`; validate connectivity on startup and fail fast with a clear
    error if unreachable or misconfigured.
  - **FR-037**: MUST persist runtime state needed to resume safely after
    container restarts (e.g., pending challenge sessions, next prompt times)
    using PostgreSQL as the source of truth; YAML is only for static config. On
    startup, resume schedules idempotently.
  - **FR-038**: SHOULD expose a simple readiness/health indicator (e.g., logs a
    “ready” message after successful initialization) and provide clear log lines
    for major lifecycle events (startup, linking, audits, reports).
  - **FR-050**: MUST include change provenance in `config.yaml`: store a
    checksum over the canonicalized config and metadata fields such as
    `updated_at` and `updated_by` (e.g., `bot-command` or `manual-edit`). On
    startup, load configs, validate them, verify checksum, and recompute/write
    a fresh checksum for valid files. If any config fails validation, exit with
    an error indicating which file and why. If checksum mismatch is detected,
    treat the last change as manual.
  - **FR-051**: On config changes that affect scheduling (e.g., audit cadence,
    provocation interval, rate limits), MUST reconfigure schedulers and limits
    immediately without reboot when changed via commands.
  - **FR-053**: On startup, MUST validate `config.yaml`, `channels.yaml`, and
    `puzzles.yaml` against expected schema and constraints. For valid files,
    recompute and persist checksums (adopt current content). For invalid files,
    exit non‑zero with a clear error message naming the file and problems
    (missing keys, wrong types, invalid values).
  - **FR-052**: Before persisting config changes initiated via commands, MUST
    verify the on-disk checksum matches the expected value. If it does not,
    proceed to write but MUST warn the admin in the modlog (and the invoking
    chat) that a manual change was detected and has been overwritten, including
    previous vs new checksum (and optionally a brief diff summary).
  - **FR-044**: OPTIONAL: If `NATS_URL` is set, publish notable events (e.g.,
    link established, audit run summary, challenge created/responded/timeout,
    kick attempted/succeeded/failed) to NATS using a configurable subject prefix
    (env `NATS_SUBJECT_PREFIX`, default `antilurk`).
 - **FR-023**: MUST persist the channel linking graph (moderated→modlog) and
  per‑chat configuration at `$CONFIG_DIR/channels.yaml` and load/apply it on
  startup. Config files MUST be human‑readable YAML under `$CONFIG_DIR`.
  - **FR-024**: MUST operate with `$DATA_DIR` defaulting to `/data` and
    `$CONFIG_DIR` defaulting to `$DATA_DIR/config` in containerized deployments;
    both overridable via environment variables.
- **FR-025**: MUST log all stored messages to a PostgreSQL database, recording
  at minimum: message ID, time, channel, and username; and SHOULD capture other
  readily available Telegram metadata (e.g., chat ID, user ID, message type,
  reply_to message ID, edit timestamp, forward/origin info). Coverage includes
  moderated channel messages and challenge interactions used for activity
  tracking and assessments. [Note: retention duration defined in FR‑011.]
  No redaction is applied in the database; store full available content and
  metadata for future indexing/analysis (subject to platform terms of service).
  - **FR-048**: MUST maintain the following core tables in PostgreSQL:
   - `users`: one row per encountered user (user_id, username, first_seen,
     last_seen, last_interaction_at, flags/roles as needed).
   - `message_archive`: one row per message in moderated chats (see MessageArchive
     entity fields) with chat_id, user_id, message_id, timestamps, text, and
     metadata. Index on (chat_id, user_id, sent_at).
   - `provocations`: one row per provocation initiated (provocation_id,
     chat_id, user_id, created_at, scheduled_at, sent_at, responded_at,
     outcome: correct/incorrect/timeout, puzzle_id/ref, and any callback data).
  - **FR-049**: MUST provide an SQL view `user_channel_activity` with per-user,
   per-chat aggregates computed from `message_archive` and `provocations`, exposing:
   (chat_id, user_id, message_count, last_message_at, last_provocation_at).
   Use appropriate indexes to keep the view performant.

*Example of marking unclear requirements:*
- **FR-011**: System MUST retain archived messages and challenge records
  indefinitely (no automatic deletion). A cleanup/retention mechanism may be
  added in a future version.
- **FR-012**: System MUST enforce access controls for archive search
  [NEEDS CLARIFICATION: owner-only, selected moderators].
 - **FR-013**: System MUST generate simple multiple‑choice puzzles (English‑only
  in v1): either
  arithmetic (addition/subtraction/multiplication within small integers) or
  common‑sense questions with obvious correct answers. Each puzzle MUST have
  3–4 choices, be randomly ordered, and track the correct answer per session.
  Examples: “What colour is a fresh banana? Red, Purple, Yellow”; “Which has a
  high summit? Mountain, Toy train, Killer whale”.
- **FR-014**: System MUST treat any answer button press as user interaction and
  reset the user’s last‑interaction timestamp to “now”. If the answer is
  correct, respond with a short thank‑you message.
- **FR-015**: If the answer is incorrect, respond with a polite nudge (e.g.,
  “Thanks for your response… are you sure about that?”) and post a notice in
  the modlog channel with a Kick button for admins to take action.

### Key Entities *(include if feature involves data)*
- **Member**: Platform user with roles, last activity timestamp, allowlist flag.
- **ChallengeSession**: Puzzle question, choices, correct answer index, attempts,
  provocation interval, status (pending/responded‑correct/responded‑incorrect/
  timeout), deadlines, outcomes, and any admin notices sent.
 - **ChannelConfig**: Telegram chat with mode (`moderated` | `modlog`), whether it
   is linked to other channels, and related settings (e.g., inactivity threshold
   override, provocation interval override).
 - **ModLogChannel**: The configured group/supergroup chat that receives
   notifications about responses, timeouts, and audit summaries for its linked
   moderated channels.
 - **ChannelLinkToken**: Ephemeral code used for forward‑based linking between
   a moderated channel and a modlog channel; includes code, source chat ID,
   expiry, issuer, and status (unused/used/expired).
- **Announcement**: Title, link, schedule, target channels, message template.
 - **MessageArchive**: One row per message in moderated chats: message ID, author
  (username/user ID), channel (name/ID), full text (if available), content
  digest, timestamps (sent/edited), message type, reply_to ID, forward/origin
  info, attachment/file references (file_id, mime type, size), and other
  readily available Telegram metadata for future analytics.
- **ModerationAction**: Type (challenge/notify/announce), reason, actor,
  references, timestamps.

---

## Deployment & Config

 - Containerized deployment: Runs as a Docker container.
 - Config directory: `$CONFIG_DIR` defaults to `/data`; mount a volume for
  persistence. Store YAML configs directly under `$CONFIG_DIR` (e.g.,
  `channels.yaml`, `timing.yaml`). Example Portainer host bind: map
  `/volume1/telegram_antilurk_bot/data` → container `/data`.
 - Database: PostgreSQL is the system of record for persistence. Connect via
  `DATABASE_URL` environment variable; connection details must be provided at
  startup.
 - Secrets: Provide the Telegram bot token via `TELEGRAM_TOKEN`; support
  standard container secret mechanisms.
- Health & resilience: On startup, validate configuration and DB connectivity;
  on restarts, reload YAML config and resume any in‑flight challenge sessions
  and schedules from durable state.
- Timezone: Use UTC internally; allow display in a configured timezone if set
  (e.g., `TZ` env var), for timestamps in reports/messages.
- Logging: Emit operational logs to stdout/stderr suitable for `docker logs` and
  centralized collection.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed

---
  - **FR-034**: MUST persist global configuration parameters (defaults for lurk
    threshold, provocation interval, audit cadence, and provocation rate limits)
    in `$CONFIG_DIR/config.yaml`, and apply precedence: per‑chat overrides in
    `channels.yaml` > global defaults in `config.yaml` > built‑in defaults
    (14 days; 48 hours; 15 minutes; 2/hour; 15/day). Config changes applied via
    bot commands MUST take effect immediately at runtime and be persisted to
    `config.yaml` without requiring a reboot. Changes made by manually editing
    `config.yaml` MUST require `/antlurk reboot` to reload.
