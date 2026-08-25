from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

try:
    from app.models.user import User, UserRoleEnum
    from app.models.mentor import Mentor
    from app.models.refresh_token import RefreshToken
    from app.schemas.auth import UserCreate, UserResponse, TokenResponse
    from app.core.security import (
        verify_password,
        get_password_hash,
        validate_password_strength,
        normalize_username,
        validate_username,
        create_access_token,
        generate_refresh_token,
        hash_refresh_token,
        ACCESS_TOKEN_EXPIRE_MINUTES,
        REFRESH_TOKEN_EXPIRE_DAYS,
    )
except ImportError:
    from backend.app.models.user import User, UserRoleEnum
    from backend.app.models.mentor import Mentor
    from backend.app.models.refresh_token import RefreshToken
    from backend.app.schemas.auth import UserCreate, UserResponse, TokenResponse
    from backend.app.core.security import (
        verify_password,
        get_password_hash,
        validate_password_strength,
        normalize_username,
        validate_username,
        create_access_token,
        generate_refresh_token,
        hash_refresh_token,
        ACCESS_TOKEN_EXPIRE_MINUTES,
        REFRESH_TOKEN_EXPIRE_DAYS,
    )


class AuthService:
    @classmethod
    def create_user(cls, db: Session, payload: UserCreate) -> User:
        """
        Creates a new user account with normalized username and hashed password.
        """
        valid_user, user_err = validate_username(payload.username)
        if not valid_user:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=user_err
            )

        valid_pwd, pwd_errors = validate_password_strength(payload.password)
        if not valid_pwd:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="; ".join(pwd_errors)
            )

        norm_username = normalize_username(payload.username)
        existing = db.query(User).filter(func.lower(User.username) == norm_username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{norm_username}' is already in use."
            )

        # Validate role
        role_val = payload.role.upper()
        if role_val not in (UserRoleEnum.ADMIN.value, UserRoleEnum.MENTOR.value, UserRoleEnum.COUNSELLOR.value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid role '{payload.role}'. Must be ADMIN, MENTOR, or COUNSELLOR."
            )

        if payload.mentor_id is not None:
            mentor = db.query(Mentor).filter(Mentor.id == payload.mentor_id).first()
            if not mentor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mentor with ID {payload.mentor_id} not found."
                )

        user = User(
            username=norm_username,
            password_hash=get_password_hash(payload.password),
            display_name=payload.display_name.strip(),
            role=role_val,
            mentor_id=payload.mentor_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def authenticate_user(cls, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticates a user with username and password.
        Uses normalized case-insensitive username lookup.
        """
        norm_username = normalize_username(username)
        user = db.query(User).filter(func.lower(User.username) == norm_username).first()
        if not user:
            # Run dummy verification to resist timing attacks
            get_password_hash("dummy_password_for_timing")
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    @classmethod
    def create_user_tokens(cls, db: Session, user: User) -> Tuple[str, str, int]:
        """
        Issues a new JWT access token and a rotating refresh token.
        Stores only the SHA-256 hash of the refresh token in the database.
        """
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            display_name=user.display_name,
        )

        raw_refresh_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_refresh_token)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
        )
        db.add(refresh_record)
        db.commit()

        expires_in_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return access_token, raw_refresh_token, expires_in_seconds

    @classmethod
    def refresh_user_tokens(
        cls,
        db: Session,
        raw_refresh_token: str,
    ) -> Optional[Tuple[str, str, int, User]]:
        """
        Rotates an existing refresh token:
        1. Validates refresh token hash, expiration, and non-revocation.
        2. Revokes the old token.
        3. Issues a brand-new refresh token and access token.
        """
        token_hash = hash_refresh_token(raw_refresh_token)
        record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if not record:
            return None

        now = datetime.now(timezone.utc)

        # Check revocation
        if record.revoked_at is not None:
            return None

        # Check expiration (ensure comparison with timezone awareness)
        record_exp = record.expires_at
        if record_exp.tzinfo is None:
            record_exp = record_exp.replace(tzinfo=timezone.utc)

        if record_exp <= now:
            return None

        user = record.user
        if not user or not user.is_active:
            return None

        # Revoke old token
        record.revoked_at = now

        # Generate new token
        new_raw_refresh = generate_refresh_token()
        new_hash = hash_refresh_token(new_raw_refresh)
        new_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        new_record = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            created_at=now,
            expires_at=new_expires_at,
            revoked_at=None,
        )
        db.add(new_record)
        db.flush()

        record.replaced_by_id = new_record.id
        db.commit()

        new_access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            display_name=user.display_name,
        )
        expires_in_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return new_access_token, new_raw_refresh, expires_in_seconds, user

    @classmethod
    def revoke_refresh_token(cls, db: Session, raw_refresh_token: str) -> bool:
        """
        Revokes a refresh token on logout.
        """
        token_hash = hash_refresh_token(raw_refresh_token)
        record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if not record or record.revoked_at is not None:
            return False

        record.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return True

    @classmethod
    def check_username_availability(cls, db: Session, username: str) -> Tuple[bool, Optional[str]]:
        """
        Validates username syntax and checks database uniqueness.
        """
        valid_syntax, err_msg = validate_username(username)
        if not valid_syntax:
            return False, err_msg

        norm = normalize_username(username)
        existing = db.query(User).filter(func.lower(User.username) == norm).first()
        if existing:
            return False, "Username is already in use."

        return True, "Username is available."
