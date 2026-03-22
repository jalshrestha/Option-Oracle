# Option Oracle

An AI-driven options trading intelligence platform. Given a stock ticker, it runs six specialized AI agents in parallel, aggregates their analysis through a dynamic weighting engine, and returns a structured BUY/SELL/HOLD signal with strike recommendations, confidence scores, and trade rationale.

---

## How it works

Each analysis request triggers a pipeline of four parallel stages:

1. **Data ingestion** — live quotes, OHLCV history, options chains, and 62 technical indicators are pulled from Alpaca and yfinance and cached for 5 minutes.

2. **Agent analysis** — six GPT-powered agents run concurrently, each examining the stock through a different lens:

   | Agent | Model | Focus |
   |---|---|---|
   | Technical | GPT-4o | Moving averages, RSI, MACD, Bollinger Bands, VWAP, support/resistance |
   | Sentiment | GPT-4o-mini | Social media (StockTwits, Reddit), news sentiment |
   | Options Flow | GPT-4o-mini | Put/call ratios, unusual volume, smart money direction |
   | Historical | GPT-4o | Pattern recognition, seasonality, historical precedent |
   | Risk | GPT-4o | Strike selection, position sizing, Greeks-based recommendations |
   | Education | GPT-4o-mini | Plain-language explanation of the signal and trade rationale |

3. **Decision engine** — agent scores are combined using scenario-aware weights (e.g. technical analysis is weighted higher in trending markets; options flow gets more weight near earnings). The weighted score maps to a directional signal and confidence level.

4. **ML layer** — a supporting ML pipeline (LightGBM for flow prediction, Prophet for volatility forecasting, a DQN reinforcement learning agent) feeds additional signal components into the ensemble.

Results are persisted to Supabase and returned through the REST API.

---

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn |
| AI agents | OpenAI Agents SDK v0.3.0 (GPT-4o, GPT-4o-mini) |
| ML models | LightGBM, Facebook Prophet, PyTorch (DQN) |
| Market data | Alpaca API, yfinance |
| Technical analysis | stock-indicators (62 indicators) |
| Database | Supabase (PostgreSQL) |
| Configuration | Pydantic Settings, python-dotenv |
| Logging | Loguru |
| Containerization | Docker, Docker Compose |

---

## Getting started

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project (free tier works)
- An [OpenAI](https://platform.openai.com) API key
- An [Alpaca](https://alpaca.markets) paper trading account (free)

### Install

```bash
git clone https://github.com/jalshrestha/Option-Oracle.git
cd Option-Oracle/option-trading-agent
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Required for AI agents
OPENAI_API_KEY=sk-...

# Required for live market data
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret

# Optional — enables enhanced scraping
JIGSAWSTACK_API_KEY=your-jigsawstack-key
```

### Initialize the database

```bash
python scripts/init_database.py
```

### Run

```bash
python main.py
```

The API starts on `http://localhost:8080`. Interactive docs are at `/docs`.

### Run with Docker

```bash
docker-compose up
```

---

## API

Base URL: `http://localhost:8080`

| Endpoint | Description |
|---|---|
| `GET /api/v1/stocks/hot-stocks` | Trending stocks with market data and AI scores |
| `GET /api/v1/agents/{symbol}` | Full agent analysis for a symbol |
| `GET /api/v1/technical/{symbol}` | Technical indicators and chart data |
| `GET /api/v1/signals/{symbol}` | Trading signals with confidence and rationale |
| `POST /api/v1/chat` | Natural language query interface |
| `GET /health` | Health check |

See [API_SPECIFICATIONS.md](API_SPECIFICATIONS.md) for complete request/response schemas and WebSocket documentation.

---

## Project structure

```
option-trading-agent/
├── main.py                          # Entry point
├── agents/                          # AI agent implementations
│   ├── orchestrator.py              # Coordinates parallel agent execution
│   ├── technical_agent.py
│   ├── sentiment_agent.py
│   ├── flow_agent.py
│   ├── history_agent.py
│   ├── risk_agent.py
│   ├── education_agent.py
│   └── base_agent.py               # Shared parsing, validation, fallback logic
├── src/
│   ├── api/                         # FastAPI application
│   │   ├── main.py
│   │   ├── intelligent_orchestrator.py
│   │   ├── chat_router.py
│   │   └── routes/
│   ├── core/
│   │   └── decision_engine.py       # Weighted signal aggregation
│   ├── data/
│   │   ├── market_data_manager.py   # Unified data layer with caching
│   │   └── alpaca_client.py         # Alpaca + yfinance integration
│   ├── indicators/
│   │   └── technical_calculator.py  # 62 technical indicators
│   └── ml/
│       ├── ensemble_model.py
│       ├── lightgbm_flow_model.py
│       ├── prophet_volatility_model.py
│       ├── openai_sentiment_model.py
│       └── rl_trading_agent.py
├── config/
│   ├── settings.py
│   ├── constants.py                 # Signal thresholds, model names, defaults
│   ├── database.py
│   └── logging.py
└── scripts/
    ├── init_database.py
    └── supabase_schema.sql
```

---

## Agent weight system

Base weights and their scenario adjustments:

| Scenario | Technical | Sentiment | Flow | Historical |
|---|---|---|---|---|
| Default | 60% | 10% | 10% | 20% |
| High volatility | 70% | 5% | 15% | 15% |
| Low volatility | 50% | 15% | 15% | 25% |
| Strong trend | 70% | 5% | 5% | 20% |
| Range-bound | 55% | 10% | 15% | 20% |

Weights are renormalized to sum to 1.0 after scenario adjustments. The scenario is detected automatically from the technical agent's output.

---

## Documentation

| Document | Contents |
|---|---|
| [API_SPECIFICATIONS.md](API_SPECIFICATIONS.md) | REST endpoints, WebSocket, request/response schemas |
| [ARCHITECTURE_DETAILS.md](ARCHITECTURE_DETAILS.md) | Service boundaries and component interactions |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Supabase tables, indexes, and Python integration |
| [AI_AGENT_IMPLEMENTATION.md](AI_AGENT_IMPLEMENTATION.md) | Agent prompts, schemas, and orchestration logic |
| [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md) | Next.js frontend design (planned) |
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Container setup and production deployment |
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | Testing approach and coverage targets |

---

## Status

The backend API, all six agents, the ML pipeline, and the Supabase integration are implemented and operational. The Next.js frontend is designed (see [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md)) but lives in a separate repository and is not yet connected.

This project uses Alpaca's paper trading environment. No real money is involved.
