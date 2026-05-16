"""
All Pydantic request/response models used across the API.
"""
from pydantic import BaseModel


# ── Auth ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    preferred_language: str = "auto"
    country: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Chat ─────────────────────────────────────────────────────────────

class MessageRequest(BaseModel):
    content: str


# ── Users ────────────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    preferred_language: str | None = None
    country: str | None = None
