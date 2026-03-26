---
description: Run the backend test suite with coverage. Use when you want to verify tests pass before committing, after making backend changes, or to check coverage.
---

# /test — Run Backend Tests

Run the full backend test suite with coverage report.

## Steps

1. `cd` into `option-trading-agent/backend`
2. Run: `conda run -n base pytest tests/ -x --tb=short --cov=src --cov-report=term-missing --cov-fail-under=80`
3. Report results:
   - How many passed / failed / skipped
   - Coverage percentage
   - Any failing test names and their error messages
4. If tests fail, diagnose the root cause and fix — do NOT skip or mock around failures.

## Flags Reference
- `-x` — stop at first failure (fast feedback)
- `--tb=short` — concise tracebacks
- `--cov=src` — measure coverage of `src/` only
- `--cov-fail-under=80` — fail if coverage drops below 80%
- Add `-k "test_name"` to run a single test by name
