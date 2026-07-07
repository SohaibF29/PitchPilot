"""
Global Exception handling middleware for FastAPI.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.domain.exceptions import PitchPilotException

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Intercepts uncaught exceptions and structures them as API standard responses."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process requests, catching exceptions."""
        start_time = time.time()
        try:
            response = await call_next(request)
            return response
        except PitchPilotException as e:
            # Map domain exception to custom HTTP code
            status_code = 500
            if e.code == "NOT_FOUND":
                status_code = 404
            elif e.code == "UNAUTHORIZED":
                status_code = 401
            elif e.code == "BAD_REQUEST":
                status_code = 400
            elif e.code == "SERVICE_UNAVAILABLE":
                status_code = 503

            latency = (time.time() - start_time) * 1000
            logger.error(
                "Domain error in request '%s': %s (code: %s) [latency: %.2fms]",
                request.url.path,
                str(e),
                e.code,
                latency,
                extra={"path": request.url.path, "error_code": e.code, "latency_ms": latency},
            )

            return JSONResponse(
                status_code=status_code,
                content={
                    "error": {
                        "message": e.message,
                        "code": e.code,
                    }
                },
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.exception(
                "Uncaught system error in request '%s': %s [latency: %.2fms]",
                request.url.path,
                str(e),
                latency,
                extra={"path": request.url.path, "latency_ms": latency},
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "A system error occurred. Please contact technical support.",
                        "code": "INTERNAL_SERVER_ERROR",
                    }
                },
            )
        finally:
            # Set request details for structured contextvars logging
            pass
