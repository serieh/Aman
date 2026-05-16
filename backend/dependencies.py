"""
Shared FastAPI dependencies used across multiple routers.
"""
from fastapi import Request
from logger import get_logger

logger = get_logger(__name__)


def get_pool(request: Request):
    """Retrieve the asyncpg connection pool from app state."""
    logger.debug("Getting database connection pool...")
    return request.app.state.pool
