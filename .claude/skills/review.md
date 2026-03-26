---
description: Review code changes before committing or opening a PR. Checks for security issues, code quality, test coverage, and adherence to project conventions.
---

# /review — Pre-Commit Code Review

Run a thorough review of staged/unstaged changes before pushing.

## Steps

1. **See what changed**:
   ```bash
   git diff HEAD --stat
   git diff HEAD
   ```

2. **Security checklist** — flag any of these immediately:
   - Hardcoded secrets, API keys, passwords, tokens
   - `str(e)` or tracebacks returned in HTTP responses
   - Missing auth (`get_current_user`) on non-public endpoints
   - Missing rate limiter on new endpoints
   - Unvalidated path params (no `Path(...)`)
   - `allow_headers=["*"]` with `allow_credentials=True`

3. **Code quality checklist**:
   - No `console.log` / `print()` debug statements
   - No unused imports or dead code
   - No TypeScript `any` without explanation
   - No bare `except:` in Python
   - No mock data fallbacks in production code paths
   - Response models are Pydantic schemas, not raw dicts

4. **Architecture checklist**:
   - Frontend API calls go through `lib/api/client.ts`
   - Backend business logic is in services, not route handlers
   - DB queries go through repository classes
   - New components reuse existing `components/ui/` primitives

5. **Tests**:
   - New endpoints have corresponding tests
   - No test uses `any` or skips assertions
   - Run `pytest tests/ -x --tb=short` and confirm passing

6. **Git hygiene**:
   - No `.env`, `*.pem`, `*.key` files staged
   - Commit message follows imperative mood convention

7. Report findings with file:line references and suggested fixes.
