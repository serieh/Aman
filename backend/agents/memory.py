import json
import uuid
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datetime import datetime, timezone
import asyncpg


async def load_history(pool: asyncpg.Pool, chat_id: str) -> list:
    """
    Fetch all messages for a chat from the DB and convert them
    to LangChain message objects for the LLM context window.
    """
    rows = await pool.fetch(
        """
        SELECT role, content
        FROM messages
        WHERE chat_id = $1
        ORDER BY creation_date ASC
        """,
        uuid.UUID(chat_id),
    )

    history = []
    for row in rows:
        if row["role"] == "user":
            history.append(HumanMessage(content=row["content"]))
        elif row["role"] == "aman_agent":
            history.append(AIMessage(content=row["content"]))
        elif row["role"] == "system":
            # Summaries are stored as system messages
            history.append(SystemMessage(content=row["content"]))

    return history


async def save_message(
    pool: asyncpg.Pool,
    chat_id: str,
    role: str,
    content: str,
    emotional_state: dict | None = None,
    safety_flag: str | None = None,
):
    """
    Insert one message row into the messages table.
    Call twice per turn: once for the user message, once for the agent reply.
    """
    await pool.execute(
        """
        INSERT INTO messages
            (message_id, chat_id, role, content, creation_date, emotional_state, safety_flag)
        VALUES
            ($1, $2, $3, $4, $5, $6, $7)
        """,
        uuid.uuid4(),
        uuid.UUID(chat_id),
        role,
        content,
        datetime.now(timezone.utc),
        json.dumps(emotional_state) if emotional_state else None,
        safety_flag,
    )


async def update_chat_modify_date(pool: asyncpg.Pool, chat_id: str):
    await pool.execute(
        "UPDATE chats SET modify_date = $1 WHERE chat_id = $2",
        datetime.now(timezone.utc),
        uuid.UUID(chat_id),
    )