"""Password hashing (bcrypt) and JWT creation/verification."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def _to_bytes(plain: str) -> bytes:
    # bcrypt operates on the first 72 bytes; truncate defensively.
    """
    Convert plaintext to UTF-8 bytes compatible with bcrypt.
    
    Parameters:
        plain (str): Plaintext to encode.
    
    Returns:
        bytes: The first 72 UTF-8 encoded bytes of the plaintext.
    """
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    """
    Hash a plaintext password into a bcrypt-formatted string.
    
    Parameters:
        plain (str): The plaintext password to hash.
    
    Returns:
        str: The bcrypt hash of the password.
    """
    return bcrypt.hashpw(_to_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.
    
    Parameters:
        plain (str): The plaintext password to verify.
        hashed (str): The stored bcrypt password hash.
    
    Returns:
        bool: `True` if the password matches the hash, `False` otherwise.
    """
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """
    Create a signed access token for the specified subject.
    
    Parameters:
        subject (str | int): Identifier to include in the token.
        expires_minutes (int | None): Token lifetime in minutes. Uses the configured default when omitted or zero.
    
    Returns:
        str: Encoded JWT containing the subject and expiration timestamp.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Decode and validate an access token.
    
    Returns:
    	str | None: The token subject, or `None` if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
