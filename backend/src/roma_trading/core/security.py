"""
Security utilities for configuration portal authentication.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import token_bytes
from typing import Any, Dict


PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 600_000
PBKDF2_SALT_BYTES = 16


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-SHA256 with a random salt."""
    salt = token_bytes(PBKDF2_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${_b64encode(salt)}${_b64encode(dk)}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored PBKDF2 hash."""
    try:
        algo, iter_str, salt_b64, hash_b64 = password_hash.split("$")
    except ValueError:
        # Fallback: treat stored hash as plain text for backward compatibility
        return password_hash == password

    if algo != PBKDF2_ALGORITHM:
        return False

    iterations = int(iter_str)
    salt = _b64decode(salt_b64)
    expected_hash = _b64decode(hash_b64)

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected_hash)


def _sign(data: bytes, secret: bytes) -> str:
    return _b64encode(hmac.new(secret, data, hashlib.sha256).digest())


def _encode_header(header: Dict[str, Any]) -> str:
    return _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _encode_payload(payload: Dict[str, Any]) -> str:
    return _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))


@dataclass
class TokenPair:
    token: str
    expires_at: datetime


def create_jwt_token(subject: str, secret: str, expires_in_minutes: int = 120) -> TokenPair:
    header = {"alg": "HS256", "typ": "JWT"}
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_in_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}

    encoded_header = _encode_header(header)
    encoded_payload = _encode_payload(payload)
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = _sign(signing_input, secret.encode("utf-8"))

    token = f"{encoded_header}.{encoded_payload}.{signature}"
    return TokenPair(token=token, expires_at=exp)


class InvalidTokenError(Exception):
    """Raised when JWT token is invalid or expired."""


def decode_jwt_token(token: str, secret: str) -> Dict[str, Any]:
    try:
        encoded_header, encoded_payload, signature = token.split(".")
    except ValueError as exc:
        raise InvalidTokenError("invalid token format") from exc

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = _sign(signing_input, secret.encode("utf-8"))
    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidTokenError("invalid signature")

    try:
        payload_json = _b64decode(encoded_payload)
        payload = json.loads(payload_json)
    except (ValueError, json.JSONDecodeError) as exc:
        raise InvalidTokenError("invalid payload") from exc

    exp = payload.get("exp")
    if exp is None or not isinstance(exp, int):
        raise InvalidTokenError("missing exp")

    if datetime.now(timezone.utc).timestamp() > exp:
        raise InvalidTokenError("token expired")

    return payload

