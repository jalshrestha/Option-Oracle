---
description: Tail and filter Docker logs for the backend, frontend, or database. Use when debugging errors, monitoring requests, or watching live output.
---

# /logs — View Service Logs

Stream or search logs from any running service.

## Live tail (backend)
```bash
docker compose logs -f backend --tail=50
```

## Errors only
```bash
docker compose logs backend --tail=200 | grep -E "ERROR|Exception|Traceback|500"
```

## Specific request (by path or symbol)
```bash
docker compose logs backend --tail=500 | grep "AAPL"
docker compose logs backend --tail=500 | grep "POST /api/v1/auth"
```

## All services
```bash
docker compose logs -f --tail=30
```

## Database logs
```bash
docker compose logs postgres --tail=50
```

## Clear and re-watch (fresh start)
```bash
docker compose restart backend && docker compose logs -f backend --tail=20
```

## Log file on disk (inside container)
```bash
docker exec -it option-trading-agent-backend-1 tail -f logs/neural_oracle.log
```

## Check what's using port 8080 (if backend won't start)
```bash
lsof -ti:8080
```
