"""
Authentication endpoints — register and login.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException

from schemas.requests import RegisterRequest, LoginRequest
from auth.utils import hash_password, verify_password, create_access_token
from dependencies import get_pool
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
async def register_user(body: RegisterRequest, pool=Depends(get_pool)):
    logger.info(f"Registration attempt | email: {body.email}")

    existing = await pool.fetchval(
        "SELECT user_id FROM users WHERE email = $1", body.email
    )
    if existing:
        logger.warning(f"Registration failed | email already exists: {body.email}")
        raise HTTPException(status_code=409, detail="Email already registered.")

    hashed = hash_password(body.password)

    user_id = await pool.fetchval(
        """
        INSERT INTO users (name, email, password, preferred_lang, country)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING user_id
        """,
        body.name,
        body.email,
        hashed,
        body.preferred_language,
        body.country,
    )

    token = create_access_token({"user_id": str(user_id)})
    logger.info(f"User registered successfully | user_id: {user_id}")

    return {
        "user_id": str(user_id),
        "token": token,
        "name": body.name,
        "email": body.email,
    }


@router.post("/login")
async def login_user(body: LoginRequest, pool=Depends(get_pool)):
    logger.info(f"Login attempt | email: {body.email}")

    row = await pool.fetchrow(
        "SELECT user_id, name, email, password FROM users WHERE email = $1",
        body.email,
    )

    if not row or not verify_password(body.password, row["password"]):
        logger.warning(f"Login failed | email: {body.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"user_id": str(row["user_id"])})
    logger.info(f"User logged in | user_id: {row['user_id']}")

    return {
        "user_id": str(row["user_id"]),
        "token": token,
        "name": row["name"],
        "email": row["email"],
    }
