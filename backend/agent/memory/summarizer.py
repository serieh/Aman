import json

from django.db.models import Max

from agent.llm import llm_summarize
from logger import get_logger 

logger = get_logger(__name__)

def _format_messages_to_string(messages, summary) -> str:
    """Format Django Message instances (and optional Summary) into a string for LLM."""
    logger.debug(f"Formatting {len(messages)} messages for summary")

    lines = []
    for msg in messages:
        role = msg.role.capitalize()
        content = msg.content

        emotional_state = msg.emotional_state
        if isinstance(emotional_state, str):
            try:
                emotional_state = json.loads(emotional_state)
            except (json.JSONDecodeError, TypeError):
                emotional_state = None

        safety_flag = msg.safety_flag
        line = f"{role}: {content}"

        if emotional_state and isinstance(emotional_state, dict):
            line += f" [Emotion: {emotional_state.get('emotion', '?')}, Confidence: {emotional_state.get('confidence', '?')}]"
        if safety_flag:
            line += f" [Safety: {safety_flag}]"

        lines.append(line)

    if summary:
        summary_emotional = summary.emotional_state or {}
        if isinstance(summary_emotional, str):
            try:
                summary_emotional = json.loads(summary_emotional)
            except (json.JSONDecodeError, TypeError):
                summary_emotional = {}
        
        summary_line = f"Summary: {summary.content} \
    [Emotion: {summary_emotional.get('emotion', '?')}, Confidence: {summary_emotional.get('confidence', '?')}]\
    [Safety: {summary.safety_flag or '?'}"
        lines.insert(0, summary_line)

    logger.debug(f"Formatted messages into string with {len(lines)} lines for summary")

    return "\n".join(lines)


def run_summarization_background(chat_id: str, message_rows: list, old_summary):
    """
    Background thread target: summarizes old messages and archives them.
    Uses Django ORM (thread-safe) for all DB operations.
    """
    from django.db import close_old_connections
    from chats.models import Message, Summary

    mid = len(message_rows) // 2
    old_messages = message_rows[:mid]
    
    logger.info(f"Summarization task started | chat_id: {chat_id} | messages_to_compress: {len(old_messages)}")
    
    try:
        old_messages_string = _format_messages_to_string(old_messages, old_summary)
        
        logger.debug(f"Passing context to LLM summarizer | chat_id: {chat_id}")
        summary = llm_summarize(old_messages_string)
        
        last_version = (
            Summary.objects.filter(chat_id=chat_id)
            .aggregate(v=Max("version"))["v"]
            or 0
        )

        Summary.objects.create(
            chat_id=chat_id,
            content=summary["content"],
            emotional_state=summary.get("emotional_state"),
            safety_flag=summary.get("safety_flag"),
            version=last_version + 1,
        )

        old_ids = [msg.message_id for msg in old_messages]
        Message.objects.filter(message_id__in=old_ids).update(is_active=False)
        
        logger.info(f"Summarization complete | chat_id: {chat_id} | new_version: {last_version + 1} | archived_messages: {len(old_ids)}")

    except Exception as e:
        logger.error(f"Summarization task failed | chat_id: {chat_id} | error: {str(e)}")
    finally:
        close_old_connections()
