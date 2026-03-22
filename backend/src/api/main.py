"""
Neural Options Oracle++ FastAPI Main Application
"""
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config.settings import settings
from config.logging import setup_logging, log_api_access, get_api_logger
from config.database import health_check as db_health_check, engine, create_tables, AsyncSessionLocal
from src.api.dependencies import get_current_session
from src.api.middleware.request_id import RequestIDMiddleware
from src.api.routes import analysis, trading, education, portfolio, system
from src.api.chat_router import router as chat_router
from src.api.intelligent_orchestrator import IntelligentOrchestrator

logger = get_api_logger()

# Singleton — created once at startup, reused across all requests
_orchestrator: IntelligentOrchestrator = None


def get_orchestrator() -> IntelligentOrchestrator:
    return _orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global _orchestrator

    # Startup
    logger.info("Starting Neural Options Oracle++ API Server")

    # Setup logging
    setup_logging()

    # Create tables (dev mode); in production Alembic runs migrations
    if settings.env != "production":
        await create_tables()

    # Verify database connection
    db_health = await db_health_check()
    if db_health["status"] != "healthy":
        logger.error(f"Database connection failed: {db_health}")
        raise Exception("Database connection failed")

    # Initialize shared orchestrator once
    _orchestrator = IntelligentOrchestrator()
    logger.info("IntelligentOrchestrator singleton initialized")

    logger.info("Database connection established")
    logger.info("Neural Options Oracle++ API Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Neural Options Oracle++ API Server")
    await engine.dispose()


# ---------------------------------------------------------------------------
# App factory helpers
# ---------------------------------------------------------------------------

def _register_middleware(app: FastAPI) -> None:
    """Register all middleware in reverse call-stack order (last = outermost)."""
    # TrustedHost: only in production; "0.0.0.0" is not a valid hostname
    if settings.env == "production":
        allowed = getattr(settings, "allowed_hosts", ["localhost", "127.0.0.1"])
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # RequestIDMiddleware runs outermost — every handler has request.state.request_id
    app.add_middleware(RequestIDMiddleware)

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            log_api_access(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=process_time,
                user_agent=user_agent,
                ip_address=client_ip,
            )
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-API-Version"] = "1.0.0"
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {request.method} {request.url.path} - {e}")
            log_api_access(
                method=request.method,
                path=request.url.path,
                status_code=500,
                response_time=process_time,
                user_agent=user_agent,
                ip_address=client_ip,
            )
            raise HTTPException(status_code=500, detail="Internal server error")


def _register_error_handlers(app: FastAPI) -> None:
    """Register centralised exception → JSON response handlers."""
    from src.exceptions import OracleError
    from src.api.error_handlers import (
        oracle_error_handler,
        http_exception_handler as oracle_http_handler,
        unhandled_exception_handler,
    )
    app.add_exception_handler(OracleError, oracle_error_handler)
    app.add_exception_handler(HTTPException, oracle_http_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _register_routers(app: FastAPI) -> None:
    """Mount all API routers and register core endpoints."""
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])
    app.include_router(education.router, prefix="/api/v1/education", tags=["Education"])
    app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
    app.include_router(chat_router, tags=["Chat Router"])

    @app.get("/")
    async def root() -> Dict[str, Any]:
        return {
            "name": "Neural Options Oracle++ API",
            "version": "1.0.0",
            "status": "active",
            "timestamp": time.time(),
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "analysis": "/api/v1/analysis",
                "trading": "/api/v1/trading",
                "education": "/api/v1/education",
                "portfolio": "/api/v1/portfolio",
                "system": "/api/v1/system",
            },
        }

    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        db_health = await db_health_check()
        overall = "healthy" if db_health["status"] == "healthy" else "unhealthy"
        return {
            "status": overall,
            "components": {"api": "healthy", "database": db_health["status"]},
            "database_details": db_health,
            "timestamp": time.time(),
        }

    @app.post("/api/v1/session/create")
    async def create_session(request: Request, risk_profile: str = "moderate") -> Dict[str, Any]:
        import uuid
        from datetime import datetime, timedelta, timezone
        from src.repositories.sessions import SessionRepository

        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent")
        session_token = str(uuid.uuid4())

        async with AsyncSessionLocal() as db:
            try:
                repo = SessionRepository(db)
                await repo.create({
                    "session_token": session_token,
                    "ip_address": client_ip,
                    "user_agent": user_agent,
                    "risk_profile": risk_profile,
                    "preferences": {},
                    "is_active": True,
                    "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
                })
                await db.commit()
            except Exception:
                await db.rollback()
                raise

        logger.info(f"New session created: {session_token}")
        return {
            "session_token": session_token,
            "risk_profile": risk_profile,
            "expires_in": 86400,
            "created_at": time.time(),
        }

    @app.get("/api/v1/session/info")
    async def get_session_info(session: Dict = Depends(get_current_session)) -> Dict[str, Any]:
        return {
            "session_token": session["session_token"],
            "risk_profile": session.get("risk_profile", "moderate"),
            "preferences": session.get("preferences", {}),
        }


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _app = FastAPI(
        title="Neural Options Oracle++ API",
        description="AI-Driven Options Trading Intelligence Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    _register_middleware(_app)
    _register_error_handlers(_app)
    _register_routers(_app)
    return _app


app = create_app()

# Chat endpoint for frontend integration
from pydantic import BaseModel
from typing import Optional, List

class ChatMessage(BaseModel):
    message: str
    selectedStock: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    actions: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    agents_triggered: Optional[List[str]] = None

@app.post("/api/v1/chat/message", response_model=ChatResponse)
async def send_chat_message(message_data: ChatMessage):
    """Chat endpoint that connects to AI agents"""
    try:
        logger.info(f"🧠 Processing chat message: {message_data.message}")
        
        # Import the intelligent orchestrator
        from src.api.intelligent_orchestrator import IntelligentOrchestrator
        orchestrator = IntelligentOrchestrator()
        
        # Process query with intelligent orchestration
        user_context = {
            'selectedStock': message_data.selectedStock,
            'risk_profile': {'risk_level': 'moderate', 'experience': 'intermediate'}
        }
        
        orchestration_result = await orchestrator.process_user_query(
            message_data.message, 
            user_context
        )
        
        # Extract information for chat response
        ai_response = orchestration_result.get('ai_response', 'Analysis complete.')
        symbol = orchestration_result.get('symbol')
        query_type = orchestration_result.get('query_type', 'general')
        agents_triggered = orchestration_result.get('ai_agents_triggered', [])
        
        # Determine actions based on orchestration results
        actions = {}
        if symbol:
            actions['analyzeStock'] = symbol
            actions['showAnalysis'] = True
            
            # Check if this is a trading request
            if 'buy' in message_data.message.lower() or 'execute' in message_data.message.lower():
                actions['showBuyRecommendations'] = True
                actions['enableTrading'] = True
        
        # Get suggested actions from orchestrator
        suggestions = orchestration_result.get('suggested_actions', [
            "Analyze technical indicators",
            "Check trading signals", 
            "Review risk assessment",
            "Show market sentiment"
        ])
        
        # Add trading-specific suggestions if this is a trading query
        if 'buy' in message_data.message.lower() or 'execute' in message_data.message.lower():
            suggestions = [
                "View buy recommendations",
                "Execute trade",
                "Review risk assessment",
                "Check position sizing"
            ]
        
        response = ChatResponse(
            response=ai_response,
            actions=actions if actions else None,
            suggestions=suggestions,
            agents_triggered=agents_triggered
        )
        
        logger.info(f"✅ Chat response generated for {symbol}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        # Fallback response if orchestration fails
        return ChatResponse(
            response=f"I'm analyzing your request: '{message_data.message}'. Let me gather comprehensive information...",
            actions={"analyzeStock": message_data.selectedStock} if message_data.selectedStock else None,
            suggestions=["Try asking about a specific stock", "Request technical analysis", "Ask for trading signals"]
        )

# Hot stocks endpoint for frontend
@app.get("/api/v1/stocks/hot-stocks")
async def get_hot_stocks():
    """Get hot stocks with real StockTwits trending data and AI analysis"""
    try:
        logger.info("🔥 Getting REAL trending stocks from StockTwits...")
        
        # Use singleton orchestrator + web scraper
        from src.agents.web_scraper_agent import get_web_scraper_agent
        from openai import OpenAI
        import os

        orchestrator = get_orchestrator()
        
        # Web scraper uses OpenAI Responses API (browsing) — only available with OpenAI
        openai_client = None
        if settings.openai_api_key:
            openai_client = OpenAI(api_key=settings.openai_api_key)
        web_scraper = get_web_scraper_agent(openai_client)
        
        # Get REAL trending stocks from StockTwits
        logger.info("📈 Scraping StockTwits for trending stocks...")
        trending_stocks_data = await web_scraper.get_trending_stocks(limit=5)
        
        if not trending_stocks_data:
            logger.warning("No trending stocks found from StockTwits - using fallback stocks")
            symbols = ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX"]
        else:
            symbols = [stock["symbol"] for stock in trending_stocks_data]
            logger.info(f"✅ Got real trending symbols: {symbols}")
        
        async def _process_one_stock(symbol: str, trending_data) -> dict | None:
            try:
                logger.info(f"📈 Getting market data for {symbol}")
                market_data = await orchestrator.market_data_manager.get_comprehensive_data(symbol)

                quote = market_data.get('quote', {})
                current_price = float(quote.get('price', 0))
                volume = float(quote.get('volume', 0))

                logger.info(f"📊 Market data for {symbol}: price=${current_price}, volume={volume}")
                logger.info(f"📊 Quote data: {quote}")

                change = float(quote.get('change', 0))
                change_percent = float(quote.get('change_percent', 0))

                if change == 0 and change_percent == 0:
                    previous_close = float(quote.get('previous_close', current_price))
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100 if previous_close > 0 else 0

                if abs(change_percent) > 20:
                    logger.warning(f"Large change detected for {symbol}: {change_percent:.1f}% - verify data")

                if abs(change_percent) > 50:
                    logger.warning(f"Extreme change detected for {symbol}: {change_percent:.1f}% - using 0%")
                    change = 0
                    change_percent = 0

                historical = market_data.get('historical', [])
                if historical:
                    recent_prices = historical[-20:]
                    sparkline_data = [{"value": float(bar.get('close', current_price))} for bar in recent_prices]
                else:
                    sparkline_data = [{"value": current_price} for _ in range(20)]

                ai_signals = []
                ai_score = 50

                if trending_data:
                    sentiment = trending_data.get('sentiment', 'Neutral')
                    mentions = trending_data.get('mentions', 0)
                    ai_signals.append(f"StockTwits: {sentiment}")
                    if isinstance(mentions, str):
                        try:
                            mentions = int(mentions)
                        except ValueError:
                            mentions = 0
                    if mentions > 0:
                        ai_signals.append(f"{mentions} mentions")
                    sentiment_score = trending_data.get('sentiment_score', 0.5)
                    if sentiment_score is not None:
                        ai_score = max(ai_score, int(sentiment_score * 100))

                if change > 0:
                    ai_signals.append("Price Up")
                    ai_score += 10
                elif change < 0:
                    ai_signals.append("Price Down")
                    ai_score -= 5

                if volume > 1000000:
                    ai_signals.append("High Volume")
                    ai_score += 5

                ai_score = max(0, min(100, ai_score))

                logger.info(f"✅ Processed {symbol}: price=${current_price}, change={change}")
                return {
                    "symbol": symbol,
                    "name": (trending_data.get('name') if trending_data else None) or market_data.get('company_name', f"{symbol} Inc"),
                    "price": current_price,
                    "change": change,
                    "changePercent": change_percent,
                    "volume": volume,
                    "sparklineData": sparkline_data,
                    "aiScore": ai_score,
                    "signals": ai_signals or ["Market Data"],
                    "trending": (trending_data and trending_data.get('trending', False)) or ai_score > 75
                }
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                return None

        paired = [
            (symbols[i], trending_stocks_data[i] if trending_stocks_data and i < len(trending_stocks_data) else None)
            for i in range(len(symbols))
        ]
        results = await asyncio.gather(*[_process_one_stock(sym, td) for sym, td in paired])
        hot_stocks = [r for r in results if r is not None]
        
        logger.info(f"✅ Retrieved {len(hot_stocks)} hot stocks with real data")
        
        return {
            "stocks": hot_stocks,
            "timestamp": time.time(),
            "total_count": len(hot_stocks),
            "data_source": "stocktwits_trending_with_ai_analysis",
            "trending_source": "stocktwits.com/sentiment/most-active",
            "symbols_found": symbols
        }
        
    except Exception as e:
        logger.error(f"❌ Hot stocks API error: {e}")
        # Return empty array instead of mock data
        return {
            "stocks": [],
            "timestamp": time.time(),
            "total_count": 0,
            "data_source": "error",
            "error": str(e)
        }

# AI Agents endpoint for frontend
@app.get("/api/v1/agents/{symbol}")
async def get_agent_analysis(symbol: str):
    """Get AI agent analysis for a specific symbol"""
    try:
        logger.info(f"🤖 Getting agent analysis for {symbol}")
        
        orchestrator = get_orchestrator()

        # Use intelligent orchestrator to get agent-specific data
        user_context = {'selectedStock': symbol}
        result = await orchestrator.process_user_query(
            f"agent analysis for {symbol}",
            user_context
        )
        
        # Extract agent data for frontend component
        agent_data = result.get('frontend_data', {}).get('agent_analysis', [])
        
        return {
            "symbol": symbol,
            "agents": agent_data,
            "overall_signal": result.get('frontend_data', {}).get('trading_signals', [{}])[0].get('direction', 'HOLD') if result.get('frontend_data', {}).get('trading_signals') else 'HOLD',
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Agent analysis error for {symbol}: {e}")
        return {
            "symbol": symbol,
            "agents": [],
            "overall_signal": "HOLD",
            "timestamp": time.time(),
            "error": str(e)
        }

# Trading signals endpoint for frontend
@app.get("/api/v1/technical/{symbol}")
async def get_technical_indicators(symbol: str):
    """Get technical indicators for a symbol"""
    try:
        logger.info(f"📊 Getting technical indicators for {symbol}")
        
        orchestrator = get_orchestrator()

        # Get technical analysis
        user_context = {'selectedStock': symbol}
        result = await orchestrator.process_user_query(
            f"technical analysis indicators for {symbol}",
            user_context
        )
        
        # Extract technical data
        technical_data = result.get('frontend_data', {}).get('technical_indicators', {})
        chart_data = result.get('frontend_data', {}).get('chart_data', {})
        
        return {
            "symbol": symbol,
            "indicators": technical_data,
            "chart_data": chart_data,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Technical indicators error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Technical indicators failed: {str(e)}")

@app.get("/api/v1/signals/{symbol}")
async def get_trading_signals(symbol: str):
    """Get trading signals for a specific symbol"""
    try:
        logger.info(f"🔥 Getting real trading signals for {symbol}...")
        
        orchestrator = get_orchestrator()

        # Get comprehensive analysis from our backend
        user_context = {
            'selectedStock': symbol,
            'risk_profile': {'risk_level': 'moderate', 'experience': 'intermediate'}
        }
        
        analysis_result = await orchestrator.process_user_query(
            f"trading signals for {symbol}",
            user_context
        )
        
        # Extract trading signals from analysis
        trading_signals = analysis_result.get('frontend_data', {}).get('trading_signals', [])
        
        logger.info(f"✅ Generated {len(trading_signals)} real trading signals for {symbol}")
        
        return {
            "signals": trading_signals,
            "symbol": symbol,
            "timestamp": time.time(),
            "total_signals": len(trading_signals),
            "data_source": "ai_agent_analysis"
        }
        
    except Exception as e:
        logger.error(f"❌ Trading signals API error for {symbol}: {e}")
        return {
            "signals": [],
            "symbol": symbol,
            "timestamp": time.time(),
            "total_signals": 0,
            "data_source": "error",
            "error": str(e)
        }

# Trading command endpoint for chat
@app.post("/api/v1/chat/trade")
async def process_trading_command(message_data: ChatMessage):
    """Process trading commands from chat interface"""
    try:
        logger.info(f"🎯 Processing trading command: {message_data.message}")
        
        # Import the intelligent orchestrator
        from src.api.intelligent_orchestrator import IntelligentOrchestrator
        orchestrator = IntelligentOrchestrator()
        
        # Set up user context for trading
        user_context = {
            'selectedStock': message_data.selectedStock,
            'risk_profile': {
                'risk_level': 'moderate',
                'experience': 'intermediate',
                'max_position_size': 0.05,
                'account_balance': 100000
            }
        }
        
        # Process the trading query
        result = await orchestrator.process_user_query(message_data.message, user_context)
        
        # Extract buy agent results
        buy_agent_result = result.get('frontend_data', {}).get('buy_agent', {})
        buy_analysis = buy_agent_result.get('buy_analysis', {})
        
        # Format response for trading
        trading_response = {
            'symbol': result.get('symbol'),
            'query': message_data.message,
            'trading_analysis': {
                'recommendations': buy_analysis.get('recommendations', []),
                'execution_plan': buy_analysis.get('execution_plan', {}),
                'risk_assessment': buy_analysis.get('risk_assessment', {}),
                'confidence': buy_analysis.get('confidence', 0.0)
            },
            'ai_response': result.get('ai_response', 'Trading analysis complete.'),
            'actions': {
                'showBuyRecommendations': len(buy_analysis.get('recommendations', [])) > 0,
                'enableTrading': True,
                'symbol': result.get('symbol')
            },
            'suggestions': [
                "Review buy recommendations",
                "Execute trade",
                "Adjust position size",
                "Set stop loss"
            ],
            'agents_triggered': result.get('ai_agents_triggered', []),
            'timestamp': time.time()
        }
        
        logger.info(f"✅ Trading command processed for {result.get('symbol')}")
        return trading_response
        
    except Exception as e:
        logger.error(f"❌ Trading command error: {e}")
        return {
            'error': str(e),
            'symbol': message_data.selectedStock,
            'trading_analysis': {
                'recommendations': [],
                'execution_plan': {'status': 'error'},
                'risk_assessment': {'risk_level': 'unknown'},
                'confidence': 0.0
            },
            'ai_response': f"I encountered an error processing your trading request: {str(e)}",
            'actions': {},
            'suggestions': ["Try again", "Check symbol", "Review risk profile"],
            'timestamp': time.time()
        }


@app.post("/api/v1/options/execute")
async def execute_options_purchase(request: Dict[str, Any]):
    """Execute options purchase after user confirmation"""
    try:
        logger.info(f"🚀 Executing options purchase: {request.get('type', 'unknown')}")
        
        purchase_type = request.get('type')
        analysis = request.get('analysis', {})
        budget = request.get('budget', 0)
        symbol = request.get('symbol')
        confirmed = request.get('confirmed', False)
        
        if not confirmed:
            return JSONResponse(
                status_code=400,
                content={"error": "User confirmation required"}
            )
        
        if purchase_type == "single_option":
            # Execute single option purchase
            from src.agents.buy_agent import execute_option_buy
            
            result = await execute_option_buy(analysis, confirmed=True)
            
        elif purchase_type == "multi_options":
            # Execute multi-options portfolio purchase
            from src.agents.multi_options_buy_agent import execute_multi_options_buy
            
            portfolio_data = {"recommended_portfolio": analysis.get('recommended_portfolio', [])}
            result = await execute_multi_options_buy(portfolio_data, confirmed=True)
            
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unknown purchase type: {purchase_type}"}
            )
        
        # Log successful execution
        if result.get('status') == 'executed' or result.get('portfolio_status') == 'executed':
            logger.info(f"✅ Options purchase executed successfully: {result}")
        else:
            logger.warning(f"⚠️ Options purchase failed: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Options execution error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Execution failed: {str(e)}",
                "status": "failed"
            }
        )


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level=settings.log_level.lower()
    )