<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles: III strengthened to Strict TDD Methodology
- Added sections: Core Principles; Additional Constraints & Security; Development Workflow & Quality Gates; Governance
- Templates requiring updates: Optional — add "Tests first" prompt to tasks template
- Follow-up TODOs: Consider adding CI stub to enforce tests exist for changes
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

### III. Strict TDD Methodology (Non‑Negotiable)
TDD is mandatory and strictly enforced:
- Red‑Green‑Refactor: Always write a failing test first, implement the minimal
  change to pass, then refactor while keeping tests green.
- No code without tests: Production code must not be merged unless introduced
  by a prior failing test in the same change.
- Test hierarchy: Prefer fast unit tests; add contract/integration tests where
  behavior spans modules or external boundaries.
- Coverage gates: Aim for high, pragmatic coverage (e.g., 85%+ of units, 100%
  of critical paths). New or changed code must be exercised by tests.
- CI enforcement: PRs must run tests; failing or skipped tests block merge.
- Regressions: When a defect is found, first add a failing test reproducing it,
  then fix.

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

**Version**: 1.1.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
