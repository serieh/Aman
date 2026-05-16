"""
Chat endpoints — CRUD + send message to agent.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query

from schemas.requests import MessageRequest
from auth.dependencies import get_current_user
from agent.runner import run_agent
from dependencies import get_pool
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", status_code=201)
async def create_chat(
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """Create a new chat session for the authenticated user."""
    user_id = uuid.UUID(current_user["user_id"])

    chat_id = await pool.fetchval(
        """
        INSERT INTO chats (user_id, title)
        VALUES ($1, $2)
        RETURNING chat_id
        """,
        user_id,
        "Untitled Chat",
    )

    logger.info(f"Chat created | chat_id: {chat_id} | user_id: {user_id}")
    return {"chat_id": str(chat_id)}


@router.get("")
async def get_chats(
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """List all chats for the authenticated user, newest first."""
    user_id = uuid.UUID(current_user["user_id"])

    rows = await pool.fetch(
        """
        SELECT chat_id, title, creation_date, modify_date
        FROM chats
        WHERE user_id = $1
        ORDER BY modify_date DESC
        """,
        user_id,
    )

    logger.debug(f"Fetched {len(rows)} chats for user_id: {user_id}")
    return [
        {
            "chat_id": str(row["chat_id"]),
            "title": row["title"],
            "creation_date": row["creation_date"].isoformat(),
            "modify_date": row["modify_date"].isoformat(),
        }
        for row in rows
    ]


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """Get all messages for a specific chat. Verifies ownership."""
    user_id = uuid.UUID(current_user["user_id"])
    chat_uuid = uuid.UUID(chat_id)

    # Verify ownership
    owner = await pool.fetchval(
        "SELECT user_id FROM chats WHERE chat_id = $1", chat_uuid
    )
    if owner is None:
        raise HTTPException(status_code=404, detail="Chat not found.")
    if owner != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    rows = await pool.fetch(
        """
        SELECT message_id, role, content, creation_date, emotional_state, safety_flag
        FROM messages
        WHERE chat_id = $1 AND is_active = TRUE
        ORDER BY creation_date ASC
        """,
        chat_uuid,
    )

    logger.debug(f"Fetched {len(rows)} messages for chat_id: {chat_id}")
    return {
        "chat_id": chat_id,
        "messages": [
            {
                "message_id": str(row["message_id"]),
                "role": row["role"],
                "content": row["content"],
                "creation_date": row["creation_date"].isoformat(),
                "emotional_state": row["emotional_state"],
                "safety_flag": row["safety_flag"],
            }
            for row in rows
        ],
    }


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """Delete a chat and all its messages/summaries (via CASCADE). Verifies ownership."""
    user_id = uuid.UUID(current_user["user_id"])
    chat_uuid = uuid.UUID(chat_id)

    owner = await pool.fetchval(
        "SELECT user_id FROM chats WHERE chat_id = $1", chat_uuid
    )
    if owner is None:
        raise HTTPException(status_code=404, detail="Chat not found.")
    if owner != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    await pool.execute("DELETE FROM chats WHERE chat_id = $1", chat_uuid)
    logger.info(f"Chat deleted | chat_id: {chat_id} | user_id: {user_id}")


@router.post("/{chat_id}/message")
async def send_message(
    chat_id: str,
    body: MessageRequest,
    background_tasks: BackgroundTasks,
    model_preference: str = Query(default="2", description="1 = thinking, 2 = fast"),
    current_user: dict = Depends(get_current_user),
    pool=Depends(get_pool),
):
    """Send a message to a chat and get the agent's response."""
    user_id_str = current_user["user_id"]
    user_id = uuid.UUID(user_id_str)
    chat_uuid = uuid.UUID(chat_id)

    logger.info(f"Chat execution started | chat_id: {chat_id} | user_id: {user_id} | model: {model_preference}")

    # Verify ownership
    owner = await pool.fetchval(
        "SELECT user_id FROM chats WHERE chat_id = $1", chat_uuid
    )
    if owner is None:
        raise HTTPException(status_code=404, detail="Chat not found.")
    if owner != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Safety pre-filter (run before agent)
    # flag = pre_filter(body.content)
    # if flag == "RED":
    #     return crisis_response(current_user["country"])

    try:
        logger.debug(f"Passing context to LangGraph agent | chat_id: {chat_id}")
        reply = await run_agent(
            pool=pool,
            user_id=user_id_str,
            chat_id=chat_id,
            user_message=body.content,
            background_tasks=background_tasks,
            model_preference=model_preference,
        )
        logger.info(f"Agent execution completed | chat_id: {chat_id}")
        return {"reply": reply}

    except Exception as e:
        logger.error(f"Agent execution failed | chat_id: {chat_id} | error: {str(e)}")
        raise HTTPException(status_code=500, detail="Aman encountered an internal error.")
