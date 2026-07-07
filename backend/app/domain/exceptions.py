"""
Domain exceptions for PitchPilot.
"""

from __future__ import annotations


class PitchPilotException(Exception):
    """Base exception for PitchPilot application."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class EntityNotFoundException(PitchPilotException):
    """Raised when an expected domain entity is not found."""

    def __init__(self, entity_name: str, identifier: str) -> None:
        super().__init__(
            f"{entity_name} with identifier '{identifier}' not found.",
            code="NOT_FOUND",
        )


class UnauthorizedException(PitchPilotException):
    """Raised on authentication or authorization failure."""

    def __init__(self, message: str = "Unauthorized access.") -> None:
        super().__init__(message, code="UNAUTHORIZED")


class InvalidRequestException(PitchPilotException):
    """Raised when input validation or business rules are violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="BAD_REQUEST")


class ServiceUnavailableException(PitchPilotException):
    """Raised when an external service is unavailable or circuit breaker trips."""

    def __init__(self, service_name: str, message: str = "") -> None:
        detail = f": {message}" if message else "."
        super().__init__(
            f"External service '{service_name}' is currently unavailable{detail}",
            code="SERVICE_UNAVAILABLE",
        )


class SecurityException(PitchPilotException):
    """Raised on encryption or cryptographic failures."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="SECURITY_ERROR")


class GraphException(PitchPilotException):
    """Raised when LangGraph execution fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="GRAPH_EXECUTION_ERROR")
