# Option Oracle — Project Status Plan

**Last updated:** 2026-03-26
**Branch:** `refactor/code-quality-performance`

---

## Legend
- ✅ Done — fully implemented, wired end-to-end
- 🟡 Partial — core logic exists but has gaps
- ❌ Not done — missing or placeholder only

---

## FRONTEND

### Pages
| Page | Status | Notes |
|------|--------|-------|
| `/landing` | ✅ | WebGL lightning, hero, feature items, CTAs → `/auth` |
| `/auth` | ✅ | Login + register tabs, JWT auth, guest flow, social OAuth placeholders |
| `/` (Dashboard) | ✅ | All widgets wired to real API; proper empty/error states |
| `/analyze/[symbol]` | ✅ | Real API calls; proper error state (no mock fallback) |
| `/chat` | ✅ | Real API; shows "unavailable" message on error (no fake response) |
| `/chain` | ✅ | Wired to `GET /api/v1/options/{symbol}`; symbol search; error state |
| `/learn` | ✅ | Wired to education endpoints (content, glossary, learning path) |
| `/system` | ✅ | Wired to `useSystemHealth`, `useSystemMetrics`, `useLLMProvider` |
| `/portfolio` | ✅ | Real positions; performance chart shows empty state if no history |

### Dashboard Widgets
| Component | Status | Notes |
|-----------|--------|-------|
| `HotStocksGrid` | ✅ | Real API; skeleton on load; proper error/empty state |
| `MarketPulseCard` | 🟡 | Filters hot-stocks for SPY/QQQ/IWM — shows empty if not returned |
| `RecentSignals` | ✅ | Wired to `GET /api/v1/analysis/signals/recent`; empty state if no data |
| `ActiveSessionCard` | ✅ | Real portfolio data; shows `$0.00` / `0` on empty |
| `SystemHealthCard` | ✅ | Real `useSystemHealth()` hook |
| `QuickAnalyze` | ✅ | Routes to `/analyze/[symbol]` |

### Auth / Layout
| Item | Status | Notes |
|------|--------|-------|
| `AuthProvider` | ✅ | JWT storage, auto-anon register, token refresh |
| `AppShell` — flash fix | ✅ | `return null` blocks paint until auth resolves |
| `AppShell` — anon redirect | ✅ | Sends anon users to `/landing` |

### Build Health
| Item | Status | Notes |
|------|--------|-------|
| `AnalysisResult` type alias | ✅ | `export type AnalysisResult = AnalysisResponse` in `types.ts` |
| TypeScript strict mode | ✅ | `ignoreBuildErrors: false` in `next.config.mjs` |

---

## BACKEND

### Authentication & Security
| Item | Status | Notes |
|------|--------|-------|
| JWT access + refresh tokens | ✅ | `python-jose`, bcrypt passwords |
| `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me` | ✅ | Full auth flow |
| `get_current_user` dependency | ✅ | Decodes Bearer JWT |
| CORS `allow_headers` | ✅ | Explicit list (no wildcard) |
| Security headers middleware | ✅ | X-Content-Type-Options, X-Frame-Options, etc. |
| `backtrace/diagnose` gated on env | ✅ | Only verbose in non-production |
| `DATABASE_URL` required (no default) | ✅ | Validator enforces `postgresql+asyncpg://` |
| Rate limiting | 🟡 | In-memory only — resets on restart; not persistent |
| Remove `str(e)` from responses | 🟡 | Inline endpoints in `main.py` may still expose some |
| TrustedHostMiddleware | 🟡 | Production only; staging not covered |
| Full traceback to disk logs | 🟡 | `error_handlers.py` — check if prod-gated |

### API Endpoints
| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /health` | ✅ | Public health check |
| `POST /api/v1/analysis/analyze/{symbol}` | ✅ | Full ML ensemble pipeline |
| `GET /api/v1/technical/{symbol}` | ✅ | Real TA-Lib indicators |
| `GET /api/v1/signals/{symbol}` | ✅ | Real DB signals |
| `GET /api/v1/analysis/signals/recent` | ✅ | Across-all-symbols; used by dashboard |
| `GET /api/v1/stocks/hot-stocks` | 🟡 | Real data; SPY/QQQ/IWM not guaranteed in response |
| `GET /api/v1/options/{symbol}` | 🟡 | Alpaca data; TODO: "replace with real trading API" |
| `POST /api/v1/chat/message` | ✅ | OpenAI-powered chat |
| `GET /api/v1/portfolio/summary` | ✅ | Real positions + P&L |
| `GET /api/v1/portfolio/performance` | ✅ | Returns real totals + cumulative daily P&L history from closed positions |
| `GET /api/v1/education/content` | 🟡 | Falls back to mock data if DB empty |
| `GET /api/v1/system/health` | ✅ | Real service checks |
| `GET /api/v1/system/metrics` | 🟡 | Mock CPU/memory stats |
| `GET /api/v1/system/logs` | ❌ | Mock implementation only |
| `GET /api/v1/system/config` | ❌ | No auth guard; leaks env info |
| `POST /api/v1/options/execute` | ❌ | Paper trade simulation — not real brokerage |

### Database
| Item | Status | Notes |
|------|--------|-------|
| PostgreSQL schema (10 tables) | ✅ | Users, signals, positions, orders, etc. |
| Alembic migrations | ✅ | Initial schema + users table |
| `performance_history` time-series | ❌ | Backend never computes/returns per-day P&L |
| DB credentials in docker-compose | ❌ | `oracle:oracle_dev` hardcoded — should use env var |

---

## ML / AI

| Component | Status | Notes |
|-----------|--------|-------|
| Ensemble orchestration | ✅ | 6 components parallel, dynamic weights |
| GPT-4o-mini sentiment scoring | ✅ | Real OpenAI calls |
| Technical analysis (TA-Lib) | ✅ | Real indicators |
| Prophet volatility forecasting | 🟡 | Real but requires 30+ days history |
| LightGBM options flow | 🟡 | Rule-based fallback; no trained `.cbm` artifact |
| RL trading agent | ❌ | Code exists; no saved weights; not trained |
| Training data pipeline | ❌ | No scripts for building datasets |
| Model retraining workflow | ❌ | No scheduled retraining or tracking |

---

## INFRASTRUCTURE

| Item | Status | Notes |
|------|--------|-------|
| Docker Compose (Postgres + backend) | ✅ | Health checks, volumes |
| Frontend dev server | ✅ | `pnpm dev` port 3000 |
| Backend container | ✅ | Port 8080, Python 3.11 |
| DB password in docker-compose | ❌ | Hardcoded `oracle:oracle_dev` |
| CI/CD pipeline | ❌ | No GitHub Actions |
| Frontend production Dockerfile | ❌ | No containerized frontend build |
| Reverse proxy (nginx/traefik) | ❌ | Not configured |

---

## TESTS

| Item | Status | Notes |
|------|--------|-------|
| Backend unit + integration + e2e tests | ✅ | ML, agents, indicators, routes |
| Auth route tests (`/register`, `/login`, `/refresh`) | ❌ | Not yet covered |
| Frontend tests | ❌ | No test files at all |

---

## WHAT'S ACTUALLY LEFT (Prioritized)

### ✅ Completed (2026-03-26)
- ~~Full frontend/backend audit — confirmed most pages already wired to real APIs~~
- ~~Enable TypeScript strict build (`ignoreBuildErrors: false` in `next.config.mjs`)~~
- ~~PLAN.md created with accurate project status~~
- ~~SPY/QQQ/IWM already appended to hot-stocks symbols list in `main.py` (was already done)~~
- ~~Add `performance_history` time-series to `GET /api/v1/portfolio/performance` — real cumulative P&L from closed positions grouped by date~~
- ~~Add `get_closed()` method to `PositionRepository`~~

### 🔴 Next Up

### 🟡 Security Hardening

3. **Move DB password to env var** in `docker-compose.yml` (`POSTGRES_PASSWORD=${POSTGRES_PASSWORD}`)
4. **Add auth guard** to `GET /api/v1/system/config` endpoint
5. **Scrub `str(e)` responses** from inline endpoints in `main.py`
6. **Add auth route tests** (`/register`, `/login`, `/refresh` — happy + error paths)

### 🟢 Future / Nice to Have

7. **Train LightGBM flow model** — generate training data, train, save `.cbm` artifact
8. **Train RL agent** — define reward function, run training loop, save weights
9. **Add frontend tests** — at minimum auth flow + dashboard smoke tests
10. **CI/CD** — GitHub Actions for lint + test on PR
11. **Frontend production Dockerfile**
12. **GitHub / Google OAuth** — replace UI placeholders with real OAuth flow
13. **Persistent rate limiting** — Redis-backed instead of in-memory

---

## FLOW: What a User Experiences Today

```
Visit /  →  AppShell detects anon user  →  redirect to /landing (no flash)
Landing  →  "Get Started" click  →  /auth
Auth     →  register/login  →  JWT stored  →  redirect to /
Dashboard  →  HotStocksGrid (real) | RecentSignals (real, empty if no analyses)
             MarketPulse (real IF SPY/QQQ/IWM in hot-stocks response)
/analyze/AAPL  →  real ML analysis runs (~35s) → real results displayed
/chat    →  real AI response via OpenAI
/chain   →  real options data (Alpaca, with TODO on execution)
/learn   →  real education content (DB or mock fallback if DB empty)
/system  →  real health + mock metrics
/portfolio  →  real positions, performance chart empty until first trade
```

---

## ARCHITECTURE

```
Browser (Next.js 14 App Router)
    └── /landing  →  public hero page
    └── /auth     →  JWT login/register
    └── /*        →  AppShell (auth guard, blocks flash)
              ↓
        FastAPI backend  :8080
              ├── Auth routes       → users table (PostgreSQL)
              ├── Analysis routes   → ML Ensemble → OpenAI + LightGBM + Prophet + TA-Lib
              ├── Chat routes       → OpenAI GPT-4o-mini
              ├── Portfolio routes  → positions/orders tables
              ├── Education routes  → educational_content table (+ mock fallback)
              ├── System routes     → health real / metrics mock
              └── Trading routes    → paper trade only (Alpaca sandbox)

        PostgreSQL  :5434
              └── 10 tables: users, signals, positions, orders, portfolio_metrics,
                             educational_content, stocks, sessions, cache, analytics
```
