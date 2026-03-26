---
description: Create and run database migrations with Alembic. Use when adding new tables, columns, or changing the schema.
---

# /migrate — Database Migrations

Create and apply Alembic migrations for schema changes.

## Generate a new migration (auto-detect changes)
```bash
cd option-trading-agent/backend
docker exec -it option-trading-agent-backend-1 \
  sh -c "PYTHONPATH=. alembic revision --autogenerate -m '<description>'"
```

## Apply pending migrations
```bash
docker exec -it option-trading-agent-backend-1 \
  sh -c "PYTHONPATH=. alembic upgrade head"
```

## Check current migration state
```bash
docker exec -it option-trading-agent-backend-1 \
  sh -c "PYTHONPATH=. alembic current"
```

## Roll back one step
```bash
docker exec -it option-trading-agent-backend-1 \
  sh -c "PYTHONPATH=. alembic downgrade -1"
```

## Steps for a typical schema change
1. Edit or create the SQLAlchemy model in `backend/src/models/`
2. Export the model from `backend/src/models/__init__.py`
3. Generate migration (auto-detect)
4. Review the generated file in `backend/src/migrations/versions/`
5. Apply: `alembic upgrade head`
6. Verify: connect to DB and check `\d <table_name>`

## Migration file location
`backend/src/migrations/versions/`

## Common issues
- **"Can't locate revision"** — migration file not in versions dir or import error in model
- **"Table already exists"** — migration already applied; check `alembic current`
- **Column type mismatch** — auto-generate may miss complex types; review the generated file before applying
