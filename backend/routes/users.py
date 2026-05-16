"""
User profile endpoints — view, update, delete.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException

from schemas.requests import UpdateProfileRequest
from auth.dependencies import get_current_user
from dependencies import get_pool
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """Get the authenticated user's profile."""
    user_id = uuid.UUID(current_user["user_id"])

    row = await pool.fetchrow(
        """
        SELECT user_id, name, email, preferred_language, country, creation_date
        FROM users
        WHERE user_id = $1
        """,
        user_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "user_id": str(row["user_id"]),
        "name": row["name"],
        "email": row["email"],
        "preferred_language": row["preferred_language"],
        "country": row["country"],
        "creation_date": row["creation_date"].isoformat(),
    }


@router.put("/me")
async def update_my_profile(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """Update the authenticated user's profile."""
    user_id = uuid.UUID(current_user["user_id"])

    # Build dynamic SET clause from provided fields
    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.preferred_language is not None:
        updates["preferred_language"] = body.preferred_language
    if body.country is not None:
        updates["country"] = body.country

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    # Build parameterized query
    set_parts = []
    params = []
    for i, (col, val) in enumerate(updates.items(), start=1):
        set_parts.append(f"{col} = ${i}")
        params.append(val)

    params.append(user_id)
    query = f"UPDATE users SET {', '.join(set_parts)} WHERE user_id = ${len(params)}"

    await pool.execute(query, *params)
    logger.info(f"User profile updated | user_id: {user_id} | fields: {list(updates.keys())}")

    return {"msg": "Profile updated successfully."}


@router.delete("/me", status_code=204)
async def delete_my_account(
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """Delete the authenticated user's account and all their data (via CASCADE)."""
    user_id = uuid.UUID(current_user["user_id"])

    await pool.execute("DELETE FROM users WHERE user_id = $1", user_id)
    logger.info(f"User account deleted | user_id: {user_id}")
