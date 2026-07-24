"""Shared FastAPI dependencies: current user (optional & required)."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


def _extract_token(authorization: str | None) -> str | None:
    """
    Extracts a bearer token from an Authorization header value.
    
    Parameters:
        authorization (str | None): The Authorization header value.
    
    Returns:
        str | None: The bearer token if the header has the expected format, otherwise None.
    """
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Resolve the authenticated user from an optional bearer token.
    
    Parameters:
        authorization: The optional Authorization header containing a bearer token.
    
    Returns:
        The matching User, or None when no valid token is provided or no user is found.
    """
    token = _extract_token(authorization)
    if not token:
        return None
    sub = decode_access_token(token)
    if sub is None:
        return None
    return db.get(User, int(sub))


def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    """Require an authenticated user.
    
    Returns:
    	User: The authenticated user.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Require an authenticated user with the admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
