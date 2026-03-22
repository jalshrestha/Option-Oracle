# Option Oracle

An AI-driven options trading intelligence platform.

## Repository layout

```
option-trading-agent/
├── backend/        FastAPI backend — agents, ML pipeline, market data, REST API
├── frontend/       Frontend (not yet implemented)
└── .github/        CI workflows
```

## Quick start

```bash
cd backend
cp .env.example .env   # fill in API keys
pip install -r requirements.txt
python main.py
```

API starts on `http://localhost:8080`. Interactive docs at `/docs`.

## Docker

```bash
docker-compose up
```

## Documentation

All backend documentation lives in `backend/`:

| Document | Contents |
|---|---|
| `backend/AI_AGENT_IMPLEMENTATION.md` | 6-agent system specification |
| `backend/API_SPECIFICATIONS.md` | REST + WebSocket API reference |
| `backend/ARCHITECTURE_DETAILS.md` | Service-level architecture |
| `backend/DATABASE_SCHEMA.md` | Supabase schema |
| `backend/DOCKER_DEPLOYMENT.md` | Container setup |
| `backend/TESTING_STRATEGY.md` | Testing approach |

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn |
| AI agents | OpenAI Agents SDK (GPT-4o, GPT-4o-mini) |
| ML models | LightGBM, Prophet, PyTorch (DQN) |
| Market data | Alpaca API, yfinance |
| Technical analysis | stock-indicators (62 indicators) |
| Database | Supabase (PostgreSQL) |
| Configuration | Pydantic Settings |
| Logging | Loguru |
| Containerization | Docker, Docker Compose |

## Status

Backend API, all agents, and ML pipeline are implemented. Frontend not yet built.

This project uses Alpaca's paper trading environment. No real money is involved.
