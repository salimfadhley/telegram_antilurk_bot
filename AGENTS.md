# Repository Guidelines

## Project Structure & Module Organization
- `/.specify/templates/`: Planning and spec templates used by agents.
- `/.specify/scripts/bash/`: Bash utilities that drive the workflow (e.g., feature setup, checks).
- `/.specify/memory/constitution.md`: Project constitution template and governance rules.
- `/.codex/commands/`: Codex CLI command definitions (`/specify`, `/plan`, `/tasks`, `/implement`).
- `/specs/`: Generated per‑feature artifacts (created by scripts), e.g. `specs/001-my-feature/`.

## Build, Test, and Development Commands
- Run commands via Codex CLI: `/specify <feature>`, `/plan`, `/tasks`, `/implement`.
- Run tests with uv: `uv run pytest <directory_or_file>` (e.g., `uv run pytest tests/contract`).
- Direct scripts (from repo root):
  - `bash .specify/scripts/bash/create-new-feature.sh "My feature"`: Create `specs/NNN-slug/` and (if git) a branch.
  - `bash .specify/scripts/bash/setup-plan.sh [--json]`: Initialize `plan.md` for the current feature branch.
  - `bash .specify/scripts/bash/check-task-prerequisites.sh [--json]`: Validate required docs before generating `tasks.md`.
  - `bash .specify/scripts/bash/check-implementation-prerequisites.sh [--json]`: Validate before executing tasks.

## Coding Style & Naming Conventions
- Shell: `bash`, `#!/usr/bin/env bash`, `set -e`, prefer small composable functions.
- Flags: Support `--json` for machine-readable output; `--help` for usage.
- Branches: `NNN-short-slug` (e.g., `001-bootstrap-workflow`). Enforced by `check_feature_branch`.
- Paths: Use absolute repo paths in agents; scripts derive paths via helpers in `common.sh`.

## Testing Guidelines
- Scripts: Dry-run with `--json` and inspect output keys/paths.
- Lint (optional): `shellcheck .specify/scripts/bash/*.sh` if available.
- Artifacts: Ensure `specs/NNN-*/` contains `spec.md`, `plan.md`, and any generated docs before proceeding.

## Commit & Pull Request Guidelines
- Commits: Follow Conventional Commits (`feat:`, `fix:`, `docs:`). Scope by area (e.g., `scripts`, `templates`).
- Branches: Use the feature branch created by the `/specify` phase (e.g., `002-add-contracts`).
- PRs must include: purpose, linked issue (if any), summary of generated artifacts (paths), and risks/rollbacks.
- Include examples of command outputs (especially `--json`) or screenshots when UI tooling is involved.

## Security & Configuration Tips
- Scripts write under `/specs/` and expect a git repo; they gracefully degrade without git.
- Review templates before bulk generation to ensure sensitive defaults aren’t propagated.
- Keep `.specify/memory/constitution.md` aligned with templates; update together via the `/constitution` flow.
