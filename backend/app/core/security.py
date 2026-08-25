import os
import re
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Dict, Any
import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Cryptographic password context using Argon2id with bcrypt fallback for backward compatibility
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# Supported and restricted JWT algorithm
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
if JWT_ALGORITHM != "HS256":
    raise RuntimeError(f"Unsupported JWT_ALGORITHM '{JWT_ALGORITHM}'. Pathwise strictly requires 'HS256'.")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]+$")


def get_jwt_secret_key() -> str:
    """
    Retrieves and validates the JWT signing secret strictly from environment configuration.
    Fails safely if the secret is missing or insecurely short (< 32 characters).
    """
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret.strip()) < 32:
        raise RuntimeError(
            "CRITICAL SECURITY ERROR: 'JWT_SECRET_KEY' is not set or is shorter than 32 characters. "
            "Configure a strong secret in your environment or .env file. "
            "Generate one using: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    return secret.strip()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored Argon2/bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generates an Argon2/bcrypt hash for a plain password."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validates that password meets institutional security requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    errors: List[str] = []
    if len(password) < 8:
        errors.append("Password must contain at least 8 characters.")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number.")
    return len(errors) == 0, errors


def normalize_username(username: str) -> str:
    """Normalizes username by trimming whitespace and lowercasing."""
    if not username:
        return ""
    return username.strip().lower()


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validates username format:
    - 3 to 30 characters
    - Letters, numbers, underscores, and periods only
    - No leading/trailing spaces
    """
    if not username or len(username.strip()) < 3:
        return False, "Username must contain at least 3 characters."
    if len(username.strip()) > 30:
        return False, "Username cannot exceed 30 characters."
    if not USERNAME_REGEX.match(username.strip()):
        return False, "Username can only contain letters, numbers, periods and underscores."
    return True, None


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    display_name: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token containing minimal claims.
    Never includes password, password hash, or sensitive student records.
    """
    secret_key = get_jwt_secret_key()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "display_name": display_name,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and verifies a signed JWT access token.
    Restricts algorithm strictly to HS256 and requires 'exp', 'iat', and 'sub'.
    Raises jwt.PyJWTError if invalid, tampered, or expired.
    """
    secret_key = get_jwt_secret_key()
    return jwt.decode(
        token,
        secret_key,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub"]},
    )


def generate_refresh_token() -> str:
    """Generates a high-entropy cryptographically random refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Computes SHA-256 hash of the refresh token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
