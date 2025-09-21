<!--
Sync Impact Report
- Version change: 1.1.0 → 1.1.1
- Modified principles: VI. Test Tooling Standard enhanced with pytest fixture guidance
- Added sections: Environment Management and Mocking guidelines under Test Tooling
- Templates requiring updates: None (clarification of existing testing practices)
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
Generate contracts and integration scenarios from specs. The standard testing
framework is pytest. Maintain tests under `tests/contract/`,
`tests/integration/`, and `tests/unit/` as suggested by plan.md. Contract
changes require updated tests.

### V. Simplicity, Observability, Versioning
Prefer the simplest viable approach (YAGNI). Emit structured, readable logs.
Breaking changes require semantic versioning (MAJOR.MINOR.PATCH) and migration
notes in PRs.

### VI. Test Tooling Standard
- Framework: pytest for all unit/contract/integration tests.
- Conventions: `pytest -q` default, `-k` for focused runs; prefer fixtures over
  ad-hoc setup; use markers for slow/integration.
- Environment Management: Use pytest's built-in fixtures for test isolation:
  * `monkeypatch` fixture for environment variable and attribute patching
  * `tmp_path` fixture for temporary file operations
  * `capsys`/`capfd` fixtures for stdout/stderr capture
  * Never manually restore environment state in finally blocks
- Mocking: Use pytest-mock (`mocker` fixture) or unittest.mock appropriately;
  prefer dependency injection and fixtures over extensive mocking.

### VII. Code Quality & Hooks (Enforced)
- Lint/format: Use ruff to keep code tidy and consistent. Code must be formatted
  with `ruff format`; linting rules may be incrementally adopted but formatting
  is mandatory.
- Types: Use mypy to ensure type consistency. Treat mypy errors as blockers.
- Hooks: Enforce ruff+mypy via pre-commit hooks (uv/uvx driven). Contributors
  must install and run hooks locally; CI should verify hooks (or equivalent
  commands) to prevent regressions.

### VIII. Style Preferences
- Unit tests: Prefer simple function-style pytest tests over class-based tests
  (e.g., `test_*.py` with plain functions and fixtures). Use classes only when
  shared state or parametrization patterns truly benefit from them.
- CLI parsing: Prefer the Click library for command-line interfaces and admin
  tools. Favor straightforward commands/subcommands with clear `--help` docs
  and consistent option names.

### IX. Property‑Based Testing (Selective)
- Use Hypothesis when it adds clear value (e.g., config parsing edge cases,
  scheduling/rate‑limit logic, text/markup rendering). Keep it targeted to
  critical logic rather than blanket usage. Reproduce found failures with
  explicit examples.

### X. Documentation Standard
- Author and maintain hierarchical Markdown docs under `docs/` (top‑level
  index plus subtopics). Each feature should update or add docs explaining
  behavior, configuration, operations, and troubleshooting. Prefer runnable
  snippets and clear examples.

### XI. Typing Policy & Stubs
- Strengthen typing over time. Prefer adding stub files (`.pyi`) or local stub
  packages for third‑party libs over sprinkling `# type: ignore`.
- Place project stubs in `stubs/` (or a dedicated typed package) and configure
  mypy to include it. Include `py.typed` for this project to signal typed code.
- Minimize `ignore` usage; if unavoidable, add a short justification.

### XII. Exception Handling Principles
- Raise as specifically as possible, catch as generally as you need — but only
  where handling is appropriate.
  - Raise precise exception types close to the source so intent is clear and
    diagnostics remain rich.
  - Avoid `except Exception:`. Catch only the exception types you anticipate
    and are prepared to handle, using multiple `except` clauses if needed.
  - At application boundaries (e.g., CLI entry points), catching broadly may be
    acceptable to present a friendly message; preserve traceback in development
    and re‑raise or exit cleanly without hiding errors.
  - Prefer exception chaining (`raise NewError(...) from e`) when adding
    context.

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

## Error Handling & Test Failures (Policy)
- No blanket `except Exception:` in production or tests unless immediately
  re-raising the original exception. Prefer catching the narrowest expected
  exception types.
- Never swallow tracebacks. Handlers must preserve context (either by not
  catching at all, or by using `raise` without arguments inside an `except` to
  re-raise).
- Integration tests must not convert genuine failures (e.g., connection
  refused) into skips. Use explicit precondition checks up front (e.g., skip
  when required env vars are missing), then let unexpected errors fail loudly
  with full tracebacks.
- Skips are only allowed for unmet, detectable preconditions (e.g., missing
  `DATABASE_URL`) — not for runtime failures.
- Prefer failing fast with clear assertions/messages over defensive
  try/except blocks that hide root causes.

## Governance
This constitution supersedes ad-hoc practices. Amendments require a PR with
rationale, version bump, and migration notes if behavior changes. Reviewers
must verify compliance (principles, gates, structure). Deviations require a
filled "Complexity Tracking" section in plan.md with explicit justification.

**Version**: 1.2.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-21
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
