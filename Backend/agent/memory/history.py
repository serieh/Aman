import json, threading
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from chats.models import Message, Summary, Chat
from django.utils import timezone

from agent.memory.summarizer import run_summarization
from ..config import MAX_MESSAGES_BEFORE_SUMMARY
from logger import get_logger

logger = get_logger(__name__)


def load_history(chat_id: str, mode: str = "normal") -> list:
    from django.db import close_old_connections
    close_old_connections()
    logger.debug(f"History load started | chat_id: {chat_id} | mode: {mode}")

    limit = 12 if mode == "voice" else 20
    all_rows = list(
        Message.objects.select_related("chat").filter(chat_id=chat_id, is_active=True)
        .exclude(safety_flag="UNSAFE")
        .order_by("-creation_date")[:limit]
    )
    rows = list(reversed(all_rows))

    logger.debug(f"Fetched {len(rows)} messages from DB for chat_id={chat_id}")

    logger.debug("Fetching last summary for chat_id=%s", chat_id)
    last_summary = (
        Summary.objects.filter(chat_id=chat_id)
        .order_by("-version")
        .first()
    )
    logger.debug(f"Last summary fetched: {last_summary}")

    logger.debug("Constructing message history for chat_id=%s", chat_id)
    history = []
    if last_summary:
        content = last_summary.content

        if last_summary.emotional_state:
            emotion = last_summary.emotional_state
            if isinstance(emotion, str):
                try:
                    emotion = json.loads(emotion)
                except json.JSONDecodeError:
                    emotion = {}
            if isinstance(emotion, dict) and emotion:
                top_emotions = ", ".join(f"{k}={int(v * 100)}%" for k, v in list(emotion.items())[:3])
                content += f"\n[User emotions during previous conversations: {top_emotions}]"
        history.append(SystemMessage(content=content))

    for row in rows:
        if row.role == "user":
            content = row.content
            if row.emotional_state:
                emotion = row.emotional_state
                if isinstance(emotion, str):
                    try:
                        emotion = json.loads(emotion)
                    except json.JSONDecodeError:
                        emotion = {}
                if isinstance(emotion, dict) and emotion:
                    top_emotions = ", ".join(f"{k}={int(v * 100)}%" for k, v in list(emotion.items())[:3])
                    content += f"\n[User emotions during this message: {top_emotions}]"
            history.append(HumanMessage(content=content))
            
        elif row.role == "assistant":
            history.append(AIMessage(content=row.content))
        elif row.role == "system":
            history.append(SystemMessage(content=row.content))

    total_chars = sum(len(m.content) for m in history)
    logger.info(f"History loaded | chat_id: {chat_id} | messages: {len(history)} | total_chars: {total_chars}")

    if len(rows) >= MAX_MESSAGES_BEFORE_SUMMARY:
        logger.info(f"Message limit exceeded ({len(rows)} >= {MAX_MESSAGES_BEFORE_SUMMARY}), triggering summarization | chat_id: {chat_id}")
        threading.Thread(
            target=run_summarization,
            args=(chat_id, rows, last_summary),
            daemon=True,
        ).start()

    logger.debug(f"Constructed message history with {len(history)} messages and total {total_chars} characters for chat_id={chat_id}")

    return history


def save_message(
    chat_id: str,
    role: str,
    content: str,
    emotional_state: dict | None = None,
    safety_flag: str | None = None,
    message_id: str | None = None,
    persona_id: str | None = None,
):
    from django.db import close_old_connections
    close_old_connections()

    log_meta = f"Saving message | chat_id: {chat_id} | role: {role}"
    if safety_flag:
        log_meta += f" | flag: {safety_flag}"
    if emotional_state and isinstance(emotional_state, dict):
        top_emotion = next(iter(emotional_state), "unknown")
        log_meta += f" | emotion: {top_emotion}"

    logger.debug(log_meta)

    kwargs = {
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "emotional_state": emotional_state if emotional_state else None,
        "safety_flag": safety_flag,
        "persona_id": persona_id,
        "is_active": True,
    }
    if message_id:
        kwargs["message_id"] = message_id

    Message.objects.create(**kwargs)
    logger.debug("Message saved successfully")


def update_chat_modify_date(chat_id: str):
    from django.db import close_old_connections
    close_old_connections()
    Chat.objects.filter(chat_id=chat_id).update(modify_date=timezone.now())
    logger.debug("Chat modify_date updated successfully")
