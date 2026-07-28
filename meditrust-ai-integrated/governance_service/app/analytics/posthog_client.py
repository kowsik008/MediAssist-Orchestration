"""
governance_service/app/analytics/posthog_client.py
----------------------------------------------------
Thin PostHog wrapper with timeout enforcement and connection-failure detection.
Returns a bool indicating whether the event was successfully sent.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from governance_service.app.config import settings
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)


class PostHogClient:
    """
    Sends events to PostHog with configurable timeout.
    Returns False (instead of raising) on any failure so the adapter
    can cascade to SQLite.
    """

    def __init__(self) -> None:
        self._client: Optional[Any] = None
        self._available: bool = False
        self._last_failure: Optional[str] = None

        if settings.POSTHOG_ENABLED and settings.POSTHOG_PROJECT_TOKEN:
            self._try_init()

    def _try_init(self) -> None:
        try:
            from posthog import Posthog  # type: ignore

            self._client = Posthog(
                project_api_key=settings.POSTHOG_PROJECT_TOKEN,
                host=settings.POSTHOG_HOST,
                timeout=settings.POSTHOG_TIMEOUT_SECONDS,
                disable_geoip=True,
            )
            # Disable automatic flushing in dev/test modes
            if settings.APP_ENV != "production":
                self._client.debug = False

            self._available = True
            log.info("PostHog client initialised.", extra={"host": settings.POSTHOG_HOST})

        except ImportError:
            self._last_failure = "posthog package not installed"
            log.warning("PostHog package not installed; will use fallback.")
        except Exception as exc:
            self._last_failure = str(exc)
            log.warning("PostHog init failed; will use fallback.", extra={"error": str(exc)})

    @property
    def is_available(self) -> bool:
        return self._available and self._client is not None

    def capture(
        self,
        distinct_id: str,
        event: str,
        properties: Dict[str, Any],
    ) -> bool:
        """
        Send a capture event.
        Returns True on success, False on any failure.
        """
        if not self.is_available:
            return False

        try:
            start = time.perf_counter()
            self._client.capture(
                distinct_id=distinct_id,
                event=event,
                properties=properties,
            )
            latency = int((time.perf_counter() - start) * 1000)
            log.debug("PostHog event captured.", extra={"event": event, "latency_ms": latency})
            return True

        except Exception as exc:
            self._available = False
            self._last_failure = str(exc)
            log.warning(
                "PostHog capture failed; marking unavailable.",
                extra={"error": str(exc), "event": event},
            )
            return False

    def flush(self) -> None:
        if self.is_available:
            try:
                self._client.flush()
            except Exception:
                pass

    def status(self) -> Dict[str, Any]:
        return {
            "available": self._available,
            "last_failure": self._last_failure,
            "host": settings.POSTHOG_HOST if settings.POSTHOG_ENABLED else "disabled",
        }
