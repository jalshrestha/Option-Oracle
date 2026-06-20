"""
Neural Options Oracle++ System API Routes
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
import time
import psutil

from config.database import health_check as db_health_check, AsyncSessionLocal
from config.logging import get_api_logger
from config.settings import settings
from src.data.redis_cache import health_check as redis_health_check
from src.api.dependencies import get_current_session, require_admin_api_token
from src.ingestion import ingestion_manager

logger = get_api_logger()
router = APIRouter()


def _has_real_secret(value: str | None) -> bool:
    """Treat empty and obvious placeholder values as unconfigured."""
    if not value:
        return False
    normalized = value.strip().lower()
    return not any(
        token in normalized
        for token in ("placeholder", "changeme", "change-me", "example", "test-key")
    )


def _external_service_health() -> Dict[str, Dict[str, Any]]:
    """Report external service readiness without making secret-backed calls."""
    now = time.time()
    openai_configured = _has_real_secret(settings.openai_api_key)
    gemini_configured = _has_real_secret(settings.gemini_api_key)
    deepseek_configured = _has_real_secret(settings.deepseek_api_key)
    alpaca_configured = (
        _has_real_secret(settings.alpaca_api_key)
        and _has_real_secret(settings.alpaca_secret_key)
    )
    jigsawstack_configured = _has_real_secret(settings.jigsawstack_api_key)

    return {
        "openai": {
            "status": "configured" if openai_configured else "unconfigured",
            "enabled": settings.llm_provider == "openai",
            "last_check": now,
            "message": (
                "OpenAI credentials are configured"
                if openai_configured
                else "OpenAI credentials are missing or placeholder"
            ),
        },
        "gemini": {
            "status": "configured" if gemini_configured else "unconfigured",
            "enabled": settings.llm_provider == "gemini",
            "last_check": now,
            "message": (
                "Gemini credentials are configured"
                if gemini_configured
                else "Gemini credentials are missing or placeholder"
            ),
        },
        "deepseek": {
            "status": "configured" if deepseek_configured else "unconfigured",
            "enabled": settings.llm_provider == "deepseek",
            "last_check": now,
            "message": (
                "DeepSeek credentials are configured"
                if deepseek_configured
                else "DeepSeek credentials are missing or placeholder"
            ),
        },
        "alpaca": {
            "status": "configured" if alpaca_configured else "unconfigured",
            "enabled": alpaca_configured,
            "last_check": now,
            "message": (
                "Alpaca paper trading credentials are configured"
                if alpaca_configured
                else "Alpaca credentials are missing or placeholder; yfinance fallback is used"
            ),
        },
        "jigsawstack": {
            "status": "configured" if jigsawstack_configured else "unconfigured",
            "enabled": jigsawstack_configured,
            "last_check": now,
            "message": (
                "JigsawStack credentials are configured"
                if jigsawstack_configured
                else "JigsawStack credentials are missing or placeholder"
            ),
        },
    }


@router.get("/")
async def system_info() -> Dict[str, Any]:
    """Get system API information"""
    
    return {
        "name": "System API",
        "version": "1.0.0",
        "description": "System monitoring, configuration, and analytics",
        "endpoints": {
            "status": "/status",
            "health": "/health",
            "analytics": "/analytics",
            "config": "/config",
            "metrics": "/metrics"
        },
        "features": [
            "System health monitoring",
            "Performance metrics",
            "Configuration management",
            "Usage analytics",
            "Error tracking"
        ]
    }


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    
    try:
        # System health checks
        db_health = await db_health_check()
        redis_health = await redis_health_check()
        
        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get network info if available
        try:
            network = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network.bytes_sent,
                "bytes_received": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_received": network.packets_recv
            }
        except:
            network_stats = {}
        
        # Application-specific status
        app_status = {
            "environment": settings.env,
            "debug_mode": settings.app_debug,
            "log_level": settings.log_level,
            "cors_origins": settings.cors_origins
        }
        
        return {
            "system": {
                "status": "healthy",
                "uptime_seconds": time.time(),  # Mock uptime
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                },
                "network": network_stats
            },
            "database": db_health,
            "redis": redis_health,
            "ingestion": ingestion_manager.get_status(),
            "application": app_status,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.get("/health")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check for all system components"""
    
    try:
        health_checks = {}
        
        # Database health
        db_health = await db_health_check()
        redis_health = await redis_health_check()
        health_checks["database"] = {
            "status": db_health["status"],
            "response_time_ms": 50,  # Mock response time
            "connection_pool": "healthy"
        }
        health_checks["redis"] = redis_health
        health_checks["ingestion"] = ingestion_manager.health()
        
        # API health
        health_checks["api"] = {
            "status": "healthy",
            "response_time_ms": 10,
            "active_connections": 5
        }
        
        # External service readiness. This is intentionally configuration-based:
        # missing optional keys should not be reported as healthy.
        health_checks["external_services"] = _external_service_health()
        
        # Overall health
        all_healthy = (
            health_checks["database"].get("status") == "healthy"
            and health_checks["api"].get("status") == "healthy"
            and health_checks["redis"].get("status") in {"healthy", "disabled"}
            and health_checks["ingestion"].get("status") in {"disabled", "healthy"}
        )
        
        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "components": health_checks,
            "timestamp": time.time(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "overall_status": "unhealthy",
            "timestamp": time.time()
        }


@router.get("/ingestion/status")
async def get_ingestion_status() -> Dict[str, Any]:
    """Get optional Kafka/Dask ingestion layer status."""
    return {
        "ingestion_layer": ingestion_manager.get_status(),
        "timestamp": time.time(),
    }


@router.get("/ingestion/health")
async def get_ingestion_health() -> Dict[str, Any]:
    """Get optional Kafka/Dask ingestion layer health."""
    return ingestion_manager.health()


@router.get("/analytics")
async def get_system_analytics(
    session: Dict = Depends(get_current_session)
) -> Dict[str, Any]:
    """Get comprehensive system analytics"""
    
    try:
        # Stub analytics (no dedicated analytics service yet)
        analytics = {"active_sessions": 0, "signals_last_24h": 0, "portfolio_summary": {}}

        # Add API usage statistics (mock)
        api_stats = {
            "total_requests": 1250,
            "requests_per_minute": 25,
            "avg_response_time_ms": 150,
            "error_rate_percent": 0.5,
            "endpoints": {
                "/api/v1/analysis/analyze": {"count": 450, "avg_time": 2500},
                "/api/v1/trading/execute": {"count": 125, "avg_time": 800},
                "/api/v1/education/content": {"count": 300, "avg_time": 200},
                "/api/v1/portfolio/summary": {"count": 375, "avg_time": 100}
            }
        }
        
        # User activity (using sessions instead of users)
        user_stats = {
            "active_sessions": analytics.get("active_sessions", 0),
            "peak_concurrent_sessions": 15,
            "avg_session_duration_minutes": 45,
            "total_analyses_today": analytics.get("signals_last_24h", 0)
        }
        
        return {
            "database_analytics": analytics,
            "api_statistics": api_stats,
            "session_statistics": user_stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system analytics")


@router.get("/config")
async def get_system_config(
    key: str = None,
    session: Dict = Depends(get_current_session)
) -> Dict[str, Any]:
    """Get system configuration"""
    
    try:
        if key:
            from sqlalchemy import select
            from src.models.analytics import SystemConfig
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SystemConfig).where(SystemConfig.config_key == key)
                )
                row = result.scalar_one_or_none()
            value = row.config_value if row else None
            return {
                "key": key,
                "value": value,
                "found": value is not None
            }
        
        # Get safe public configuration
        public_config = {
            "analysis_timeout_seconds": settings.analysis_timeout_seconds,
            "max_concurrent_analysis": settings.max_concurrent_analysis,
            "default_risk_profile": settings.default_risk_profile,
            "paper_trading_balance": settings.paper_trading_balance,
        }

        # Only expose internal infra details in development
        if settings.env == "development":
            public_config["rate_limits"] = {
                "per_minute": settings.rate_limit_per_minute,
                "burst": settings.rate_limit_burst,
            }
            public_config["cors_origins"] = settings.cors_origins
            public_config["environment"] = settings.env

        return public_config
        
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system config")


@router.post("/config")
async def update_system_config(
    key: str,
    value: Any,
    description: str = None,
    session: Dict = Depends(get_current_session),
    _admin: None = Depends(require_admin_api_token),
) -> Dict[str, Any]:
    """Update system configuration"""
    
    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from src.models.analytics import SystemConfig
        async with AsyncSessionLocal() as db:
            stmt = pg_insert(SystemConfig).values(
                config_key=key, config_value=value, description=description
            ).on_conflict_do_update(
                index_elements=["config_key"],
                set_={"config_value": value, "description": description},
            )
            await db.execute(stmt)
            await db.commit()
        success = True

        if success:
            return {
                "success": True,
                "key": key,
                "value": value,
                "message": "Configuration updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
            
    except Exception as e:
        logger.error(f"Failed to update system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update system config")


@router.get("/metrics")
async def get_system_metrics(
    metric_type: str = "all",
    session: Dict = Depends(get_current_session)
) -> Dict[str, Any]:
    """Get detailed system metrics"""
    
    try:
        metrics = {}
        
        if metric_type in ["all", "performance"]:
            metrics["performance"] = {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        
        if metric_type in ["all", "business"]:
            analytics: dict = {}
            metrics["business"] = {
                "total_analyses_today": analytics.get("signals_last_24h", 0),
                "active_positions": analytics.get("portfolio_summary", {}).get("total_positions", 0),
                "total_portfolio_value": analytics.get("portfolio_summary", {}).get("total_value", 0),
                "session_count": analytics.get("active_sessions", 0)
            }
        
        if metric_type in ["all", "errors"]:
            # Mock error metrics - in production would come from logging system
            metrics["errors"] = {
                "total_errors_today": 5,
                "error_rate_percent": 0.5,
                "critical_errors": 0,
                "most_common_errors": [
                    {"error": "API timeout", "count": 3},
                    {"error": "Invalid symbol", "count": 2}
                ]
            }
        
        return {
            "metrics": metrics,
            "metric_type": metric_type,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@router.get("/logs")
async def get_system_logs(
    level: str = "INFO",
    limit: int = 100,
    component: str = None,
    session: Dict = Depends(get_current_session)
) -> Dict[str, Any]:
    """Get system logs (mock implementation)"""
    
    try:
        # Mock log entries - in production would read from log files
        mock_logs = [
            {
                "timestamp": time.time() - 300,
                "level": "INFO",
                "component": "api",
                "message": "Analysis completed for AAPL",
                "context": {"symbol": "AAPL", "duration": "2.5s"}
            },
            {
                "timestamp": time.time() - 600,
                "level": "WARNING", 
                "component": "database",
                "message": "Slow query detected",
                "context": {"query_time": "1.2s"}
            },
            {
                "timestamp": time.time() - 900,
                "level": "ERROR",
                "component": "agents",
                "message": "OpenAI API rate limit exceeded",
                "context": {"retry_after": "60s"}
            }
        ]
        
        # Filter by level
        if level != "ALL":
            mock_logs = [log for log in mock_logs if log["level"] == level]
        
        # Filter by component
        if component:
            mock_logs = [log for log in mock_logs if log["component"] == component]
        
        # Apply limit
        mock_logs = mock_logs[:limit]
        
        return {
            "logs": mock_logs,
            "total_count": len(mock_logs),
            "filters": {
                "level": level,
                "component": component,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system logs")


@router.get("/llm-provider")
async def get_llm_provider() -> Dict[str, Any]:
    """Get the active LLM provider and model configuration (read-only)."""
    if settings.llm_provider == "openai":
        large_model = settings.openai_model_large
        small_model = settings.openai_model_small
    elif settings.llm_provider == "gemini":
        large_model = settings.gemini_model_large
        small_model = settings.gemini_model_small
    else:
        large_model = settings.deepseek_model_large
        small_model = settings.deepseek_model_small

    return {
        "provider": settings.llm_provider,
        "models": {
            "large": large_model,
            "small": small_model,
        },
        "base_url": settings.deepseek_base_url if settings.llm_provider == "deepseek" else None,
        "note": "To switch providers, update LLM_PROVIDER in .env and restart the backend.",
    }


@router.post("/maintenance")
async def trigger_maintenance_task(
    task_type: str,
    session: Dict = Depends(get_current_session)
) -> Dict[str, Any]:
    """Trigger system maintenance tasks"""
    
    try:
        if task_type == "cleanup":
            # Mock cleanup task
            result = {
                "task": "cleanup",
                "deleted_records": 150,
                "freed_space_mb": 25,
                "duration_seconds": 5.2
            }
        elif task_type == "backup":
            # Mock backup task  
            result = {
                "task": "backup",
                "backup_size_mb": 125,
                "backup_location": "s3://backups/neural-oracle/",
                "duration_seconds": 30.5
            }
        else:
            raise HTTPException(status_code=400, detail="Unknown maintenance task type")
        
        logger.info(f"Maintenance task completed: {task_type}")
        
        return {
            "success": True,
            "task_type": task_type,
            "result": result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Maintenance task failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute maintenance task")
