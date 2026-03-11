"""
Auth utilities: password hashing, JWT creation/verification, API key generation.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import jwt
from passlib.context import CryptContext

from apps.api.app.core.config import settings

# ── Passwords ────────────────────────────────────────────────────────────────

# passlib CryptContext — preferred for Phase 2+
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ───────────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _secret_key() -> str:
    """Return SECRET_KEY from settings; falls back to a dev-only key with a warning."""
    import warnings
    key = settings.SECRET_KEY
    if not key:
        warnings.warn(
            "SECRET_KEY is not configured. Set it via the SECRET_KEY environment variable "
            "before deploying to production.",
            RuntimeWarning,
            stacklevel=3,
        )
        return "dev-insecure-key-change-in-production"
    return key


def create_access_token(
    user_id: str,
    is_superadmin: bool = False,
    business_id: str | None = None,
    *,
    data: dict | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Supports two calling styles:
    - create_access_token(user_id, is_superadmin, business_id)   — legacy
    - create_access_token(data={"sub": ...}, expires_delta=...)  — Phase 2 style
    """
    if expires_delta is not None:
        expire = _now() + expires_delta
    else:
        expire = _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    if data is not None:
        payload = {**data, "exp": expire, "iat": _now(), "type": "access"}
    else:
        payload = {
            "sub": user_id,
            "iat": _now(),
            "exp": expire,
            "type": "access",
            "superadmin": is_superadmin,
            "business_id": business_id,
        }
    return jwt.encode(payload, _secret_key(), algorithm=settings.ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, hash). Store only the hash."""
    raw = secrets.token_urlsafe(48)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return raw, h


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def decode_access_token(token: str) -> dict:
    """Raises JWTError on invalid/expired token."""
    return jwt.decode(token, _secret_key(), algorithms=[settings.ALGORITHM])


def decode_token(token: str) -> dict:
    """Alias for decode_access_token — Phase 2 interface."""
    return decode_access_token(token)


# ── API Keys ──────────────────────────────────────────────────────────────────
# Format: wf_<prefix8>_<random48>
# Store SHA-256 hash of the full key; prefix is shown for identification.

API_KEY_PREFIX = "wf_"


def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, key_prefix, key_hash)."""
    rand = secrets.token_urlsafe(36)
    prefix = rand[:8]
    full_key = f"{API_KEY_PREFIX}{prefix}_{rand}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


def hash_api_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()
