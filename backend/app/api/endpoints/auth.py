from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.models.user import User, UserRoleEnum
    from app.schemas.auth import (
        LoginRequest,
        RefreshTokenRequest,
        UserCreate,
        UserResponse,
        TokenResponse,
        UsernameCheckResponse,
    )
    from app.services.auth import AuthService
    from app.api.deps import get_current_user, require_role
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.models.user import User, UserRoleEnum
    from backend.app.schemas.auth import (
        LoginRequest,
        RefreshTokenRequest,
        UserCreate,
        UserResponse,
        TokenResponse,
        UsernameCheckResponse,
    )
    from backend.app.services.auth import AuthService
    from backend.app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates user with username and password.
    Returns short-lived JWT access token and rotating refresh token.
    Uses generic error message on failure to prevent username enumeration.
    """
    user = AuthService.authenticate_user(
        db=db,
        username=payload.username,
        password=payload.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token, expires_in = AuthService.create_user_tokens(db=db, user=user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Rotates refresh token and issues a new access token.
    Old refresh token is permanently revoked.
    """
    res = AuthService.refresh_user_tokens(
        db=db,
        raw_refresh_token=payload.refresh_token,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token, new_refresh_token, expires_in, user = res

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Revokes the provided refresh token on logout.
    """
    AuthService.revoke_refresh_token(db=db, raw_refresh_token=payload.refresh_token)
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns profile information for the currently authenticated user.
    """
    return UserResponse.model_validate(current_user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_account(
    payload: UserCreate,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """
    ADMIN only: Creates a new user account (ADMIN, MENTOR, or COUNSELLOR).
    """
    user = AuthService.create_user(db=db, payload=payload)
    return UserResponse.model_validate(user)


@router.get("/check-username", response_model=UsernameCheckResponse, status_code=status.HTTP_200_OK)
def check_username(
    username: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Live setup validation endpoint: checks username syntax and availability.
    """
    available, msg = AuthService.check_username_availability(db=db, username=username)
    return UsernameCheckResponse(
        username=username,
        available=available,
        message=msg,
    )
