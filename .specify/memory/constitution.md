<!--
Sync Impact Report
- Version change: N/A → 1.0.0
- Modified principles: N/A (initial version)
- Added sections: Core Principles; Additional Constraints & Security; Development Workflow & Quality Gates; Governance
- Templates requiring updates: ✅ .specify/templates/plan-template.md (aligned); ✅ .specify/templates/spec-template.md (aligned); ✅ .specify/templates/tasks-template.md (aligned); ✅ .codex/commands/* (no outdated references)
- Follow-up TODOs: None
-->

# Mind of Steele Bot Constitution

## Core Principles

### I. Library-First Modules
Every feature starts as a small, self-contained module with a clear purpose.
Modules must be independently testable and documented before integration into
the wider structure proposed in plan.md.

### II. CLI/Text I-O Interfaces
Tools expose functionality via CLI with text protocols: stdin/args → stdout,
errors → stderr. Where applicable, support a `--json` flag for machine output.
Absolute paths must be used in agent output.

### III. Test-First (Non‑Negotiable)
TDD is mandatory. Write tests first so they fail, then implement to pass,
following the task order in tasks.md. Red‑Green‑Refactor is strictly enforced.

### IV. Contracts & Integration Testing
Generate contracts and integration scenarios from specs. Maintain tests under
`tests/contract/`, `tests/integration/`, and `tests/unit/` as suggested by
plan.md. Contract changes require updated tests.

### V. Simplicity, Observability, Versioning
Prefer the simplest viable approach (YAGNI). Emit structured, readable logs.
Breaking changes require semantic versioning (MAJOR.MINOR.PATCH) and migration
notes in PRs.

## Additional Constraints & Security
- Default runtime is workspace-write with restricted network; avoid networked
  dependencies unless explicitly approved.
- Scripts must support `--json` and avoid destructive actions without consent.
- Use absolute repository paths in agent outputs; scripts derive paths via
  `.specify/scripts/bash/common.sh`.
- All generated artifacts live under `specs/NNN-slug/` tied to a feature branch
  `NNN-short-slug`.

## Development Workflow & Quality Gates
1. `/specify`: Create feature branch and `specs/NNN-slug/spec.md`.
2. `/plan`: Produce `plan.md`; generate `research.md`, `data-model.md`,
   `contracts/`, `quickstart.md` (gated by Constitution Check).
3. `/tasks`: Create ordered `tasks.md` using design artifacts.
4. `/implement`: Execute tasks in order, respecting [P] parallelism rules.

Quality gates: Constitution Check passes; research complete; tests exist and
fail before implementation; tasks.md fully executed; docs updated.

## Governance
This constitution supersedes ad-hoc practices. Amendments require a PR with
rationale, version bump, and migration notes if behavior changes. Reviewers
must verify compliance (principles, gates, structure). Deviations require a
filled "Complexity Tracking" section in plan.md with explicit justification.

**Version**: 1.0.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
