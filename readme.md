# Option Oracle

Option Oracle is an AI-assisted options analysis and paper-trading app. It combines market data, technical analysis, sentiment/flow checks, risk controls, and a chat interface for asking stock and options questions.

The app is built for research and paper trading. It is not financial advice and does not enable live trading by default.

## Features

- AI chat for quotes, stock analysis, options-flow questions, and risk-managed trade ideas
- LangGraph-backed chat orchestration with live progress events
- Stock analysis with technical, sentiment, options-flow, history, risk, and education agents
- Options chain and technical indicator endpoints
- Paper trade recommendations with confirmation before execution
- Portfolio summary, greeks, risk, positions, and performance views
- System health, Redis status, provider status, and Prometheus metrics
- FastAPI backend, PostgreSQL, Redis, and Next.js frontend

## Repository Layout

```text
option-trading-agent/
├── backend/              FastAPI backend, agents, data providers, persistence, tests
├── Frontend/             Next.js frontend
├── docker-compose.yml    Local Postgres, Redis, backend, and optional frontend stack
└── readme.md
```

## Requirements

- Python 3.11 or 3.12
- Node.js and pnpm
- Docker Desktop, if using the Docker stack
- PostgreSQL and Redis, either locally or through Docker Compose

## Environment

Create local environment files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp Frontend/.env.example Frontend/.env.local
```

Generate a JWT secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Core backend settings:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `REDIS_URL`
- `LLM_PROVIDER`
- `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY`
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`

External keys are optional for basic local startup, but AI and broker-backed behavior will degrade when they are missing. The system health endpoint reports missing providers as `unconfigured`.

## Run Locally

Start the backend:

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Backend URLs:

- API: `http://localhost:8080`
- OpenAPI docs: `http://localhost:8080/docs`
- Health: `http://localhost:8080/health`

Start the frontend:

```bash
cd Frontend
pnpm install
pnpm run dev
```

Frontend URL:

- `http://localhost:3000`

## Docker

Start the local backend stack:

```bash
docker compose up -d --build postgres redis backend
```

Optionally run the frontend container:

```bash
docker compose --profile frontend up -d --build
```

## Testing

Backend:

```bash
cd backend
. .venv/bin/activate
python -m pytest
```

Frontend:

```bash
cd Frontend
pnpm run lint
pnpm test
pnpm run build
```

Docker image checks:

```bash
docker build -t option-oracle-backend:test ./backend
docker build --target test -t option-oracle-backend-test:test ./backend
docker build -t option-oracle-frontend:test ./Frontend
```

## API Highlights

- `POST /api/v1/chat/message`
- `POST /api/v1/chat/stream`
- `POST /api/v1/analysis/analyze/{symbol}`
- `GET /api/v1/options/{symbol}`
- `GET /api/v1/technical/{symbol}`
- `POST /api/v1/trading/analyze-buy`
- `POST /api/v1/trading/execute-recommendation`
- `GET /api/v1/portfolio/summary`
- `GET /api/v1/system/health`
- `GET /metrics`

## Safety

Option Oracle defaults to paper trading. Live trading should remain disabled unless the backend configuration, broker credentials, order flow, and risk controls have been explicitly reviewed.

Always verify prices, liquidity, expiration, max loss, and order details before placing any trade.
