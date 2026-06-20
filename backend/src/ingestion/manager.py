"""Disabled-by-default ingestion status facade.

This is the first integration slice from Sajan's Lambda Architecture layer.
It exposes the runtime contract now while keeping Kafka and Dask optional.
The heavy clients should be added behind these flags in a later phase.
"""
from datetime import datetime, timezone
from typing import Any, Dict

from config.settings import settings


class IngestionManager:
    """Report optional ingestion capability without requiring Kafka/Dask packages."""

    def __init__(self) -> None:
        self._started_at: datetime | None = None

    @property
    def is_enabled(self) -> bool:
        return settings.ingestion_kafka_enabled or settings.ingestion_dask_enabled

    def start(self) -> None:
        if self.is_enabled and self._started_at is None:
            self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        self._started_at = None

    def get_status(self) -> Dict[str, Any]:
        """Return Sajan-compatible ingestion status with graceful degradation."""
        if not self.is_enabled:
            return {
                "is_running": False,
                "status": "disabled",
                "uptime_seconds": 0,
                "kafka": self._kafka_status("disabled"),
                "dask": self._dask_status("disabled"),
                "streams": self._stream_status("disabled"),
            }

        self.start()
        uptime = (
            datetime.now(timezone.utc) - self._started_at
        ).total_seconds() if self._started_at else 0

        kafka_status = "pending" if settings.ingestion_kafka_enabled else "disabled"
        dask_status = "pending" if settings.ingestion_dask_enabled else "disabled"
        return {
            "is_running": False,
            "status": "degraded",
            "uptime_seconds": uptime,
            "kafka": self._kafka_status(kafka_status),
            "dask": self._dask_status(dask_status),
            "streams": self._stream_status(kafka_status),
            "note": "Kafka/Dask clients are not wired yet; this phase exposes the integration contract only.",
        }

    def health(self) -> Dict[str, Any]:
        status = self.get_status()
        enabled = self.is_enabled
        return {
            "healthy": not enabled,
            "status": status["status"],
            "components": {
                "kafka_producer": status["kafka"]["producer"]["status"],
                "kafka_consumer": status["kafka"]["consumer"]["status"],
                "dask_cluster": status["dask"]["cluster"]["status"],
                "market_stream": status["streams"]["market"]["status"],
                "options_stream": status["streams"]["options"]["status"],
                "sentiment_stream": status["streams"]["sentiment"]["status"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _kafka_status(status: str) -> Dict[str, Any]:
        return {
            "enabled": settings.ingestion_kafka_enabled,
            "bootstrap_servers": settings.kafka_bootstrap_servers,
            "consumer_group": settings.kafka_consumer_group,
            "producer": {"status": status, "messages_published": 0},
            "consumer": {"status": status, "messages_consumed": 0},
            "topics": {
                "market_ticks": "market-ticks",
                "options_flow": "options-flow",
                "sentiment": "sentiment-events",
                "technical": "technical-signals",
            },
        }

    @staticmethod
    def _dask_status(status: str) -> Dict[str, Any]:
        return {
            "enabled": settings.ingestion_dask_enabled,
            "scheduler_address": settings.dask_scheduler_address,
            "configured_workers": settings.dask_n_workers,
            "cluster": {"status": status, "workers": 0, "jobs_submitted": 0},
        }

    @staticmethod
    def _stream_status(status: str) -> Dict[str, Any]:
        return {
            "market": {"status": status, "subscribed_symbols": []},
            "options": {"status": status, "flows_detected": 0},
            "sentiment": {"status": status, "events_processed": 0},
        }


ingestion_manager = IngestionManager()
