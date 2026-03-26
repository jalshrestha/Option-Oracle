---
description: Debug a failing API endpoint. Use when an endpoint returns an unexpected status code, wrong data, or a 500 error.
---

# /debug-api — Debug a Failing API Endpoint

Systematically diagnose why an endpoint is broken.

## Steps

1. **Get a valid JWT first**:
   ```bash
   TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"YourPassword"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
   ```

2. **Hit the endpoint directly** and capture full response:
   ```bash
   curl -s -w "\nHTTP %{http_code}" \
     -H "Authorization: Bearer $TOKEN" \
     http://localhost:8080/api/v1/<path> | python3 -m json.tool
   ```

3. **Check backend logs** for the real error (never visible in the API response):
   ```bash
   docker compose logs --tail=100 backend | grep -E "ERROR|Exception|Traceback"
   ```

4. **Check the route** — read the route file, its dependencies, and the service it calls.

5. **Check the database** if it's a data issue:
   ```bash
   docker exec -it option-trading-agent-postgres-1 psql -U oracle -d option_oracle -c "SELECT * FROM <table> LIMIT 5;"
   ```

6. **Common root causes**:
   - `422` — path/query param validation failed; check `Path(...)` constraints
   - `401` — JWT missing, expired, or wrong type (`access` vs `refresh`)
   - `500` — unhandled exception; always in logs, never in response body
   - `503` — DB connection pool exhausted or Postgres container down

7. Report: exact error, file + line number, proposed fix.
