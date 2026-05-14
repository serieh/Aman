import asyncio
import json, uuid, asyncpg
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datetime import datetime, timezone
from .summrizer import get_summary

MAX_HISTORY_CHARS = 160000
summary_task = None


async def load_history(pool: asyncpg.Pool, chat_id: str) -> list:
    rows = await pool.fetch(
        """
        SELECT *
        FROM messages
        WHERE chat_id = $1
        ORDER BY creation_date ASC
        """,
        uuid.UUID(chat_id),
    )

    last_summary = await pool.fetchrow(
        """
        SELECT *
        FROM summaries
        WHERE chat_id = $1
        ORDER BY version DESC
        LIMIT 1
        """,
        uuid.UUID(chat_id),
    )
    history = []

    if last_summary:
        content = last_summary["content"]

        if last_summary["emotional_state"]:
            emotion = json.loads(last_summary["emotional_state"])
            content += f"\n[User appeared {emotion['emotion']} (confidence: {int(emotion['confidence'] * 100)}%) during this Summary of the previous conversations.]"
        history.append(SystemMessage(content=last_summary["content"]))

    for row in rows:
        if row["role"] == "user":
            content = row["content"]

            if row["emotional_state"]:
                emotion = json.loads(row["emotional_state"])
                content += f"\n[User appeared {emotion['emotion']} (confidence: {int(emotion['confidence'] * 100)}%) during this message.]"
            history.append(HumanMessage(content=content))
            
        elif row["role"] == "assistant":
            history.append(AIMessage(content=row["content"]))
        elif row["role"] == "system":
            history.append(SystemMessage(content=row["content"]))

    total_chars = sum(len(m.content) for m in history)
    if total_chars > MAX_HISTORY_CHARS:
        if summary_task is None or summary_task.done():
            summary_task = asyncio.create_task(get_summary(chat_id, pool, rows))
        else:
            print("Summary already in progress, skipping new summary task.")

    return history


async def save_message(
    pool: asyncpg.Pool,
    chat_id: str,
    role: str,
    content: str,
    emotional_state: dict | None = None,
    safety_flag: str | None = None,
):
    await pool.execute(
        """
        INSERT INTO messages
            (message_id, chat_id, role, content, creation_date, emotional_state, safety_flag)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
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