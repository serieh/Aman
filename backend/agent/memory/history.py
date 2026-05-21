import json
import threading
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agent.memory.summarizer import run_summarization_background
from ..config import MAX_MESSAGES_BEFORE_SUMMARY
from logger import get_logger

logger = get_logger(__name__)


def load_history(chat_id: str) -> list:
    """Load chat history from DB as LangChain message objects."""
    from chats.models import Message, Summary

    logger.debug(f"History load started | chat_id: {chat_id}")

    rows = list(
        Message.objects.filter(chat_id=chat_id, is_active=True)
        .order_by("creation_date")
    )

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
                emotion = json.loads(emotion)
            content += f"\n[User appeared {emotion['emotion']} (confidence: {int(emotion['confidence'] * 100)}%) during this Summary of the previous conversations.]"
        history.append(SystemMessage(content=content))

    for row in rows:
        if row.role == "user":
            content = row.content
            if row.emotional_state:
                emotion = row.emotional_state
                if isinstance(emotion, str):
                    emotion = json.loads(emotion)
                emo_name = emotion.get("emotion", "unknown")
                emo_conf = emotion.get("confidence", 0.0)
                
                if emo_name != "unknown":
                    content += f"\n[User appeared {emo_name} (confidence: {int(emo_conf * 100)}%) during this message.]"
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
            target=run_summarization_background,
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
):
    from chats.models import Message

    log_meta = f"Saving message | chat_id: {chat_id} | role: {role}"
    if safety_flag:
        log_meta += f" | flag: {safety_flag}"
    if emotional_state:
        log_meta += f" | emotion: {emotional_state.get('emotion', 'unknown')}"

    logger.debug(log_meta)

    Message.objects.create(
        chat_id=chat_id,
        role=role,
        content=content,
        emotional_state=emotional_state if emotional_state else None,
        safety_flag=safety_flag,
        is_active=True,
    )
    logger.debug("Message saved successfully")


def update_chat_modify_date(chat_id: str):
    from django.utils import timezone
    from chats.models import Chat

    Chat.objects.filter(chat_id=chat_id).update(modify_date=timezone.now())
    logger.debug("Chat modify_date updated successfully")
