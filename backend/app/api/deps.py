from typing import Optional
from fastapi import Depends, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Dependency extracting and verifying the JWT bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Authorization header with Bearer token is required")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token payload missing subject identifier")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise AuthenticationError("User not found or account deactivated")

    return user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency verifying that the authenticated user possesses admin privileges."""
    if current_user.role != "admin":
        raise AuthorizationError("Administrator privileges required for this action")
    return current_user
