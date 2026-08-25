from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Normalized username")
    password: str = Field(..., min_length=1, description="Plaintext password for verification")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10, description="Opaque refresh token")


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field("MENTOR", description="ADMIN, MENTOR, or COUNSELLOR")
    mentor_id: Optional[int] = Field(None, description="Optional linked mentor ID for MENTOR role")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    role: str
    mentor_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UsernameCheckResponse(BaseModel):
    username: str
    available: bool
    message: Optional[str] = None
