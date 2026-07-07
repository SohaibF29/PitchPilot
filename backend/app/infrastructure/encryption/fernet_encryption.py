"""
Fernet symmetric encryption implementation for user third-party API keys.
"""

from __future__ import annotations

import base64

from cryptography.fernet import Fernet

from app.config import get_settings
from app.domain.exceptions import SecurityException

settings = get_settings()


class FernetEncryptor:
    """Handles secure encryption and decryption of third-party API keys."""

    def __init__(self) -> None:
        raw_key = settings.encryption_key.get_secret_value()
        if not raw_key:
            # For development safety, fallback to generating a temporary key if none provided
            # WARNING: In production, settings validation should catch missing encryption key
            self._key = Fernet.generate_key()
        else:
            try:
                # Ensure key is valid base64 urlsafe
                self._key = raw_key.encode()
                # Verify key is valid for Fernet
                Fernet(self._key)
            except Exception as e:
                # If key is not base64 encoded, derive/encode it
                hashed = base64.urlsafe_b64encode(raw_key.encode()[:32].ljust(32, b"0"))
                self._key = hashed

        self._cipher = Fernet(self._key)

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt a plaintext API key.

        Args:
            plaintext: Raw API key.

        Returns:
            Encrypted bytes.
        """
        if not plaintext:
            raise SecurityException("Cannot encrypt empty key.")
        try:
            return self._cipher.encrypt(plaintext.encode("utf-8"))
        except Exception as e:
            raise SecurityException(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt encrypted API key bytes.

        Args:
            ciphertext: Encrypted key bytes.

        Returns:
            Decrypted plaintext string.
        """
        if not ciphertext:
            raise SecurityException("Cannot decrypt empty value.")
        try:
            return self._cipher.decrypt(ciphertext).decode("utf-8")
        except Exception as e:
            raise SecurityException(f"Decryption failed: {e}")


# Singleton instance
encryptor = FernetEncryptor()
