from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .utils import decode_access_token
from logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency that extracts and validates the JWT from the 
    Authorization header. Returns the decoded payload (contains user_id).
    
    Usage in endpoints:
        current_user = Depends(get_current_user)
        user_id = current_user["user_id"]
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        logger.warning("Authentication failed | invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        logger.warning("Authentication failed | token missing user_id claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )
    
    logger.debug(f"User authenticated | user_id: {user_id}")
    return {"user_id": user_id}
