import json, uuid, asyncpg
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datetime import datetime, timezone

from agent.memory.summarizer import get_summary
from config import MAX_MESSAGES_BEFORE_SUMMARY
from logger import get_logger

logger = get_logger(__name__)

async def load_history(pool: asyncpg.Pool, chat_id: str, background_tasks: BackgroundTasks,) -> list:
    logger.debug(f"History load started | chat_id: {chat_id}")
    rows = await pool.fetch(
        """
        SELECT *
        FROM messages
        WHERE chat_id = $1 AND is_active = TRUE
        ORDER BY creation_date ASC
        """,
        uuid.UUID(chat_id),
    )

    logger.debug(f"Fetched {len(rows)} messages from DB for chat_id={chat_id}")

    logger.debug("Fetching last summary for chat_id=%s", chat_id)
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
    logger.debug(f"Last summary fetched: {last_summary}")

    logger.debug("Constructing message history for chat_id=%s", chat_id)
    history = []
    if last_summary:
        content = last_summary["content"]

        if last_summary.get("emotional_state", None):
            emotion = json.loads(last_summary["emotional_state"])
            content += f"\n[User appeared {emotion['emotion']} (confidence: {int(emotion['confidence'] * 100)}%) during this Summary of the previous conversations.]"
        history.append(SystemMessage(content=content))

    for row in rows:
        if row["role"] == "user":
            content = row["content"]
            if row.get("emotional_state", None):
                emotion = json.loads(row["emotional_state"])
                emo_name = emotion.get("emotion", "unknown")
                emo_conf = emotion.get("confidence", 0.0)
                
                if emo_name != "unknown":
                    content += f"\n[User appeared {emo_name} (confidence: {int(emo_conf * 100)}%) during this message.]"
            history.append(HumanMessage(content=content))
            
        elif row["role"] == "assistant":
            history.append(AIMessage(content=row["content"]))
        elif row["role"] == "system":
            history.append(SystemMessage(content=row["content"]))

    total_chars = sum(len(m.content) for m in history)
    logger.info(f"History loaded | chat_id: {chat_id} | messages: {len(history)} | total_chars: {total_chars}")
    if len(rows) >= MAX_MESSAGES_BEFORE_SUMMARY:
        logger.info(f"Message limit exceeded ({len(rows)} >= {MAX_MESSAGES_BEFORE_SUMMARY}), triggering summarization | chat_id: {chat_id}")
        background_tasks.add_task(get_summary, chat_id, pool, rows, last_summary)

    logger.debug(f"Constructed message history with {len(history)} messages and total {total_chars} characters for chat_id={chat_id}")

    return history


async def save_message(
    pool: asyncpg.Pool,
    chat_id: str,
    role: str,
    content: str,
    emotional_state: dict | None = None,
    safety_flag: str | None = None,
):
    log_meta = f"Saving message | chat_id: {chat_id} | role: {role}"
    if safety_flag:
        log_meta += f" | flag: {safety_flag}"
    if emotional_state:
        log_meta += f" | emotion: {emotional_state.get('emotion', 'unknown')}"

    logger.debug(log_meta)

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
    logger.debug("Message saved successfully")


async def update_chat_modify_date(pool: asyncpg.Pool, chat_id: str):
    await pool.execute(
        "UPDATE chats SET modify_date = $1 WHERE chat_id = $2",
        datetime.now(timezone.utc),
        uuid.UUID(chat_id),
    )
    logger.debug("Chat modify_date updated successfully")
