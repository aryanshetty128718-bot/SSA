from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.rate_limiter import login_rate_limiter
from app.core.exceptions import AuthenticationError, ValidationException
from app.schemas.auth_admin import UserRegister, UserLogin, TokenResponse, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise ValidationException("An account with this email address already exists")

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password, returning JWT access token."""
    login_rate_limiter.check_rate_limit(request)

    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("User account has been deactivated")

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile of the currently authenticated user."""
    return current_user
