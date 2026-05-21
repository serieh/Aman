import threading
from django.db import close_old_connections
from langchain_core.messages import SystemMessage, HumanMessage

from logger import get_logger
from agent.memory.history import load_history, save_message, update_chat_modify_date
from agent.graph import GRAPH
from agent.llm import title_generator
from agent.prompts.builder import build_system_prompt


logger = get_logger(__name__)
SYSTEM_PROMPT = build_system_prompt()
logger.info("Agent runner initialized and system prompt built")


def _generate_title_background(user_message: str, chat_id: str):
    """
    Background thread target: generates a chat title via LLM and saves it.
    Uses Django ORM (thread-safe) for the DB update.
    """
    from chats.models import Chat

    logger.debug(f"Chat title generation requested | chat_id: {chat_id}")
    try:
        title = title_generator(user_message)
        logger.info(f"Chat title generation completed successfully | chat_id: {chat_id}")
        Chat.objects.filter(chat_id=chat_id).update(title=title)
    except Exception as e:
        logger.error(f"Title generation failed, defaulting to 'Untitled Chat' | chat_id: {chat_id} | error: {e}")
        try:
            Chat.objects.filter(chat_id=chat_id).update(title="Untitled Chat")
        except Exception as inner:
            logger.error(f"Fallback title update also failed | error: {inner}")
    finally:
        close_old_connections()


def run_agent(
    user_id: str,
    chat_id: str,
    user_message: str,
    # emotion_context: dict | None = None,
    safety_flag: str | None = None,
    model_preference: str = "2" 
) -> str:

    log_meta = f"Agent runner started | chat_id: {chat_id} | id: {user_id}"
    if safety_flag:
        log_meta += f" | safety_flag: {safety_flag}"
    logger.info(log_meta)

    try:
        from chats.models import Chat

        history = load_history(chat_id)

        if not history:
            chat = Chat.objects.filter(chat_id=chat_id).values_list("title", flat=True).first()
            
            # Check if it's None, empty, or default fallback
            if not chat or chat == "Untitled Chat":
                logger.info(f"No history or title found, generating title | chat_id: {chat_id}")
                threading.Thread(
                    target=_generate_title_background,
                    args=(user_message, chat_id),
                    daemon=True,
                ).start()
            else:
                logger.info(f"No history found but title exists, skipping title generation | chat_id: {chat_id}")
        else:
            logger.debug(f"History exists, skipping title generation | chat_id: {chat_id}")
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT), 
            *history,                               
            HumanMessage(content=user_message),
        ]
        
        logger.debug(f"Invoking LangGraph | chat_id: {chat_id} | context_messages: {len(messages)}")

        result = GRAPH.invoke({
            "messages": messages,
            "user_id": user_id,
            "chat_id": chat_id,
            # "emotion_context": emotion_context,
            "model_preference": model_preference,
        })

        response = result.get("response") or {}

        logger.debug(f"Persisting user and assistant messages | chat_id: {chat_id}")
        
        save_message(
            chat_id,
            role="user",
            content=user_message,
            emotional_state=response.get("emotional_state", dict()),
            safety_flag=safety_flag,
        )

        cleaned_response = (response.get("content", "")).replace("\n", "")

        save_message(
            chat_id,
            role="assistant",
            content=cleaned_response,
        )
        
        update_chat_modify_date(chat_id)
        
        logger.info(f"Agent runner completed successfully | chat_id: {chat_id}")

        return cleaned_response
        
    except Exception as e:
        logger.error(f"Agent runner failed | chat_id: {chat_id} | error: {str(e)}")
        return "Sorry, something went wrong while processing your message."
