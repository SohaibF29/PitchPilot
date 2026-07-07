"""
Security utilities for PitchPilot.

Handles API key masking, input sanitization, and security helpers.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from typing import Any


def mask_api_key(key: str) -> str:
    """
    Mask an API key for safe display, showing only last 4 characters.

    Args:
        key: The full API key.

    Returns:
        Masked string like "sk-...a1b2"
    """
    if not key or len(key) < 8:
        return "****"
    prefix = key[:3] if key.startswith(("sk-", "pk-")) else ""
    suffix = key[-4:]
    return f"{prefix}...{suffix}"


def generate_meeting_id() -> str:
    """Generate a cryptographically secure meeting ID."""
    return secrets.token_urlsafe(16)


def generate_thread_id(meeting_id: str) -> str:
    """
    Generate a deterministic thread ID from a meeting ID.

    This ensures the same meeting always maps to the same LangGraph thread.

    Args:
        meeting_id: The meeting's unique identifier.

    Returns:
        A thread ID string.
    """
    return f"thread_{meeting_id}"


def hash_key_for_lookup(key: str) -> str:
    """
    Create a hash of an API key for lookup purposes (not storage).

    Args:
        key: The API key to hash.

    Returns:
        SHA-256 hash hex string.
    """
    return hashlib.sha256(key.encode()).hexdigest()


def sanitize_input(text: str, max_length: int = 50000) -> str:
    """
    Sanitize user input text.

    - Strips leading/trailing whitespace
    - Removes null bytes
    - Truncates to max length
    - Removes control characters (except newlines and tabs)

    Args:
        text: Raw user input.
        max_length: Maximum allowed length.

    Returns:
        Sanitized text.
    """
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Remove control characters except \n and \t
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Strip whitespace
    text = text.strip()
    # Truncate
    return text[:max_length]


def is_valid_api_key_format(key: str, provider: str = "openai") -> bool:
    """
    Basic format validation for API keys.

    Args:
        key: The API key to validate.
        provider: The provider name ('openai', 'tavily').

    Returns:
        True if the key format appears valid.
    """
    if not key or len(key) < 10:
        return False

    patterns: dict[str, str] = {
        "openai": r"^sk-[a-zA-Z0-9_-]{20,}$",
        "tavily": r"^tvly-[a-zA-Z0-9_-]{10,}$",
    }

    pattern = patterns.get(provider)
    if pattern:
        return bool(re.match(pattern, key))

    # Generic validation for unknown providers
    return len(key) >= 20


def redact_dict(data: dict[str, Any], sensitive_keys: set[str] | None = None) -> dict[str, Any]:
    """
    Redact sensitive fields from a dictionary for safe logging.

    Args:
        data: Dictionary to redact.
        sensitive_keys: Set of key names to redact.

    Returns:
        New dictionary with sensitive values replaced by "***REDACTED***".
    """
    if sensitive_keys is None:
        sensitive_keys = {
            "api_key", "openai_key", "tavily_key", "secret",
            "password", "token", "authorization", "encrypted_key",
        }

    redacted = {}
    for key, value in data.items():
        if any(s in key.lower() for s in sensitive_keys):
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value, sensitive_keys)
        else:
            redacted[key] = value
    return redacted
