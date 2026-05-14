import asyncpg
from ..creator import llm_summrize
import uuid, json


def __format_messages_to_string(rows: list, summary: dict) -> str:
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

    summary_line = f"Summary: {summary['content']} \
    [Emotion: {summary.get('emotional_state', {}).get('emotion', '?')}, Confidence: {summary.get('emotional_state', {}).get('confidence', '?')}]\
    [Safety: {summary.get('safety_flag', '?')}"

    lines.insert(0, summary_line)

    return "\n".join(lines)


async def get_summary(chat_id: str, pool: asyncpg.Pool, rows: list, old_summary: dict):
    mid = len(rows) // 2
    old_messages = rows[:mid]

    old_messages_string = __format_messages_to_string(old_messages, old_summary)
    summary = await llm_summrize(old_messages_string)

    last_summary_version = await pool.fetch(
        "SELECT COALESCE(MAX(version), 0) FROM summaries WHERE chat_id = $chat_id",
        uuid.UUID(chat_id)
    )

    await pool.execute(
        "INSERT INTO Summaries (chat_id, content, emotional_state, safety_flag,"\
         " version) VALUES ($1, $2, $3, $4, $5)",
        uuid.UUID(chat_id),
        summary["content"],
        json.dumps(summary.get("emotional_state")) if summary.get("emotional_state") else None,
        summary.get("safety_flag"),
        (last_summary_version + 1)
    )

    old_ids = [row["message_id"] for row in old_messages]
    await pool.execute(
        "UPDATE messages SET is_active = $1 WHERE message_id = ANY($2)",
        False,
        old_ids
    )