---
description: Rebuild and redeploy Docker containers. Use after backend code changes, dependency updates, or when the backend is out of sync with local code.
---

# /deploy — Docker Rebuild & Deploy

Rebuild and restart the backend (and optionally frontend) Docker services.

## Steps

1. **Check current state**: `docker compose ps`
2. **Build backend**: `docker compose build backend`
3. **Restart backend**: `docker compose up -d backend`
4. **Verify health**:
   ```
   sleep 3 && curl -s http://localhost:8080/health | python3 -m json.tool
   ```
5. If health check fails, tail logs to diagnose: `docker compose logs --tail=50 backend`
6. Report: container status, health response, any errors from logs.

## When to rebuild frontend (Docker)
Only if running frontend in Docker (normally use `pnpm dev` instead):
```
docker compose build frontend && docker compose up -d frontend
```

## Full restart (all services)
```
docker compose down && docker compose up -d
```

## Common fixes
- **Port already in use**: `docker compose down` first
- **Stale image**: `docker compose build --no-cache backend`
- **DB not ready**: check `docker compose logs postgres`
