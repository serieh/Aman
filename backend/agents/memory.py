import json, uuid, asyncpg
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datetime import datetime, timezone
from .creator import summarize

MAX_HISTORY_CHARS = 60_000


def format_messages_to_string(rows: list) -> str:
    lines = []
    for row in rows:
        role = row["role"].capitalize()
        content = row["content"]

        emotional_state = row["emotional_state"]
        if isinstance(emotional_state, str):
            try:
                emotional_state = json.loads(emotional_state)
            except (json.JSONDecodeError, TypeError):
                emotional_state = None

        safety_flag = row["safety_flag"]
        line = f"{role}: {content}"

        if emotional_state and isinstance(emotional_state, dict):
            line += f" [Emotion: {emotional_state.get('emotion', '?')}, Confidence: {emotional_state.get('confidence', '?')}]"
        if safety_flag:
            line += f" [Safety: {safety_flag}]"

        lines.append(line)
    return "\n".join(lines)


async def archive_old_messages(pool: asyncpg.Pool, chat_id: str, old_messages: list, summary_id: uuid.UUID):
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO backup_messages
                    (message_id, chat_id, role, content, creation_date,
                     emotional_state, safety_flag, archived_at, summary_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                [
                    (
                        row["message_id"],
                        uuid.UUID(chat_id),
                        row["role"],
                        row["content"],
                        row["creation_date"],
                        row["emotional_state"],
                        row["safety_flag"],
                        datetime.now(timezone.utc),
                        summary_id,
                    )
                    for row in old_messages
                ],
            )
            old_ids = [row["message_id"] for row in old_messages]
            await conn.execute(
                "DELETE FROM messages WHERE message_id = ANY($1)", old_ids
            )


async def summarize_and_trim(chat_id: str, pool: asyncpg.Pool, rows: list) -> list:
    mid = len(rows) // 2
    old_messages = rows[:mid]
    kept_messages = rows[mid:]

    old_messages_string = format_messages_to_string(old_messages)
    summary = summarize(old_messages_string)

    summary_id = uuid.uuid4()
    summary_timestamp = old_messages[-1]["creation_date"]

    await pool.execute(
        """
        INSERT INTO messages
            (message_id, chat_id, role, content, creation_date, emotional_state, safety_flag)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        summary_id,
        uuid.UUID(chat_id),
        "system",                                           
        summary["content"],
        summary_timestamp,
        json.dumps(summary.get("emotional_state")) if summary.get("emotional_state") else None,
        summary.get("safety_flag"),
    )

    await archive_old_messages(pool, chat_id, old_messages, summary_id)

    history = [SystemMessage(content=summary["content"])]
    for row in kept_messages:
        if row["role"] == "user":
            history.append(HumanMessage(content=row["content"]))
        elif row["role"] == "assistant":
            history.append(AIMessage(content=row["content"]))
        elif row["role"] == "system":
            history.append(SystemMessage(content=row["content"]))

    return history


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

    history = []
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
        history = await summarize_and_trim(chat_id, pool, rows)

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