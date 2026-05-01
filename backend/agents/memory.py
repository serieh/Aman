import json, os
import psycopg2
import psycopg2.extras
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from .prompts.summary import summary_prompt

MAX_HISTORY_CHARS = 12_000

load_dotenv()
conn = psycopg2.connect(os.getenv('CONNECTION_STRING'))

def load_history(chat_id: str) -> list:
    """
    Load all messages for a chat from PostgreSQL.
    Returns them as LangChain message objects, ready to pass to the LLM.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT role, content, emotional_state, safety_flag FROM messages
            WHERE chat_id = %s
            ORDER BY creation_date ASC
            """,
            (chat_id,),
        )
        rows = cur.fetchall()

    messages = []
    for row in rows:
        if row["role"] == "user":
            messages.append(HumanMessage(content=row["content"]))
        elif row["role"] == "assistant":
            messages.append(AIMessage(content=row["content"]))
        elif row["role"] == "system":
            # Summaries are stored as system messages
            messages.append(SystemMessage(content=row["content"]))

    return messages


async def get_history_for_agent(chat_id: str, agent) -> list:
    """
    Main function to call before running the agent.
    Loads history, checks length, summarizes with the LLM if needed.
    """
    # FIX: was re-running a raw query here and getting cursor rows (not message objects)
    #      just call load_history() which already does this correctly
    messages = load_history(chat_id)

    total_chars = sum(len(m.content) for m in messages)

    if total_chars > MAX_HISTORY_CHARS:
        messages = await _summarize_and_trim(chat_id, messages, agent)

    return messages


# ── Save ───────────────────────────────────────────────────────────────────────

def save_message(
    chat_id: str,
    role: str,          # "user" or "assistant"
    content: str,
    emotional_state: dict = None,
    safety_flag: str = None,
):
    """
    Save a single message to the database.
    Call this twice per turn: once for the user message, once for the assistant response.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO messages (chat_id, role, content, emotional_state, safety_flag)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                chat_id,
                role,
                content,
                json.dumps(emotional_state) if emotional_state else None,
                safety_flag,
            ),
        )
        cur.execute(
            "UPDATE chats SET modify_date = NOW() WHERE chat_id = %s",
            (chat_id,),
        )
    conn.commit()


# ── Summarization (internal) ───────────────────────────────────────────────────

async def _summarize_and_trim(chat_id: str, messages: list, agent) -> list:
    """
    When the conversation gets too long:
    1. Take the oldest half of messages.
    2. Ask the LLM to summarize them into one compact block.
    3. Delete those old messages from the DB.
    4. Save the summary as a 'system' role message.
    5. Return [summary_message] + the recent messages untouched.
    """

    mid = len(messages) // 2
    old_messages = messages[:mid]
    recent_messages = messages[mid:]

    transcript = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Aman'}: {m.content}"
        for m in old_messages
    )
    summary_response = await agent.llm_call(summary_prompt + transcript)
    summary_text = f"[Earlier conversation summary]: {summary_response}"

    _replace_old_messages_with_summary(chat_id, len(old_messages), summary_text)

    return [SystemMessage(content=summary_text)] + recent_messages


def _replace_old_messages_with_summary(
    chat_id: str,
    count: int,
    summary_text: str,
):
    """
    Deletes the N oldest messages and inserts a summary system message
    with a timestamp just before them so it sorts first on next load.
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

        # Get IDs of the oldest N messages
        cur.execute(
            """
            SELECT message_id FROM messages
            WHERE chat_id = %s
            ORDER BY creation_date ASC
            LIMIT %s
            """,
            (chat_id, count),
        )
        ids_to_delete = [str(row["message_id"]) for row in cur.fetchall()]

        if ids_to_delete:
            placeholders = ",".join(["%s"] * len(ids_to_delete))
            cur.execute(
                f"DELETE FROM messages WHERE message_id::text IN ({placeholders})",
                ids_to_delete,
            )

        # Insert summary as a system message timestamped before all remaining messages
        cur.execute(
            """
            INSERT INTO messages (chat_id, role, content, creation_date)
            VALUES (%s, 'system', %s, (
                SELECT COALESCE(MIN(creation_date), NOW())
                FROM messages WHERE chat_id = %s
            ) - INTERVAL '1 second')
            """,
            (chat_id, summary_text, chat_id),
        )

    conn.commit()