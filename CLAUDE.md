# Claude Code — Project Instructions

## Bash & Terminal
- Bash is always allowed — no confirmation needed for any shell command.
- Chain sequential steps with `&&`; use `;` only when later steps should run regardless of failure.
- Use absolute paths in scripts; never assume `cwd`.
- Background long-running processes with `run_in_background` rather than sleeping and polling.

## Git Workflow
- Never add Claude as a co-author in commits (no `Co-Authored-By` trailer).
- Commit and push after every meaningful change — don't batch unrelated work into one commit.
- Never force-push. Never push directly to `main`. Always push to `origin/<current-branch>`.
- Commit messages: imperative mood, present tense — `add feature`, not `added feature`.
- Scope commits: one logical change per commit.
- Stage specific files by name — never `git add -A` or `git add .` (risk of committing secrets).

## Branch Convention
- Feature branches: `feat/<name>`, `fix/<name>`, `refactor/<name>`, `chore/<name>`.
- Pushes go to `origin/<current-branch>` automatically.

## Code Quality
- No unused imports, dead code, or commented-out blocks left behind.
- No `console.log` / `print()` debug statements in committed code.
- TypeScript: avoid `any` — if unavoidable, add a comment explaining why.
- Python: type hints on all function signatures; no bare `except:` clauses.
- Don't over-engineer — minimum complexity for the current task.
- Don't add docstrings, comments, or type annotations to code you didn't change.

## Testing
- Before committing backend changes: `cd backend && pytest tests/ -x --tb=short`
- Never skip failing tests — diagnose and fix the root cause.
- Keep coverage above 80%: `pytest --cov=src --cov-fail-under=80`
- Use `dependency_overrides` to stub `get_current_user` in tests — don't hit real DB.

## Security
- Never hardcode secrets, API keys, or passwords — environment variables only.
- Never commit `.env` files. Check with `git diff --cached` before every commit.
- Validate all input at API boundaries; use `Path(...)` validators on path params.
- All authenticated endpoints require `get_current_user` dependency.
- Use `Authorization: Bearer <jwt>` for all API calls from the frontend.
- Never return `str(e)` or tracebacks in HTTP responses — log server-side, return generic message.

## Architecture
- **Backend**: FastAPI + SQLAlchemy async. All DB operations via the repository pattern.
  - Routes are thin controllers — business logic belongs in services.
  - Every endpoint gets `get_rate_limiter()` and auth unless explicitly public.
- **Frontend**: Next.js 14 App Router + TypeScript.
  - All API calls go through `Frontend/lib/api/client.ts`.
  - All data fetching uses hooks from `Frontend/lib/hooks/use-api.ts`.
  - No direct `fetch()` calls inside components.
- No inline SQL — SQLAlchemy ORM only.
- No mock data fallbacks in production paths — show real error/empty states.

## Error Handling
- Frontend: always show user-friendly error states; never silent failures or `[object Object]`.
- Parse FastAPI 422 errors: `detail` is an array — join `.msg` fields before displaying.
- Custom error handler returns `{ "error": "...", "code": "..." }` — check this before `detail`.
- Backend: `logger.error(f"...: {e}", exc_info=True)` server-side; return `"An internal error occurred."` to client.

## Docker Workflow
- After backend Python changes: `docker compose build backend && docker compose up -d backend`
- After dependency changes (`requirements.txt`): same as above — full rebuild.
- Check health: `curl -s http://localhost:8080/health | python3 -m json.tool`
- Tail logs: `docker compose logs -f backend --tail=50`
- Frontend dev server: `cd Frontend && pnpm dev` (port 3000, hot-reload, no Docker needed)

## Frontend UI Rules
- Use existing components from `Frontend/components/ui/` — never create duplicates.
- Dark theme tokens: `bg-card`, `bg-muted`, `text-muted-foreground`, `border-border`.
- Primary CTAs use `brand-gradient` class (`linear-gradient(135deg, #7c6ff7, #4f46e5, #0ea5e9)`).
- Animations via `framer-motion` — use `layoutId` for shared-element transitions.
- Icons from `lucide-react` only.

## Backend API Rules
- All endpoints live under `/api/v1/`.
- Public endpoints (auth register/login, health): explicit rate limit, no auth.
- Symbol path params: `Path(..., min_length=1, max_length=5, pattern=r"^[A-Za-z]+$")`.
- Enum query params: `Literal["value1", "value2"]` — not bare `str`.
- Return typed Pydantic response models — never return raw dicts from route handlers.

## Environment
- Backend runs in Docker on port **8080**.
- Frontend dev server on port **3000**.
- DB: PostgreSQL via Docker on port **5434** (mapped from 5432 in container).
- Required env vars: `DATABASE_URL`, `JWT_SECRET_KEY`, `OPENAI_API_KEY`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`.
