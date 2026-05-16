import uuid
from fastapi import BackgroundTasks
from langchain_core.messages import SystemMessage, HumanMessage
import asyncpg

from logger import get_logger
from agent.memory.history import load_history, save_message, update_chat_modify_date
from agent.graph import GRAPH
from agent.llm import title_generator
from agent.prompts.builder import build_system_prompt


logger = get_logger(__name__)

SYSTEM_PROMPT = build_system_prompt()
logger.info("Agent runner initialized and system prompt built")

async def get_title(pool: asyncpg.Pool, user_message: str, chat_id: str) -> str:
    logger.debug("Chat title generation requested")
    try:
        title = await title_generator(user_message)
        logger.info("Chat title generation completed successfully")
        
        await pool.execute(
            "UPDATE chats SET title = $1 WHERE chat_id = $2",
            title,
            uuid.UUID(chat_id)
        )
        
    except Exception as e:
        logger.error(f"Title generation failed, defaulting to 'Untitled Chat' | error: {e}")
        await pool.execute(
            "UPDATE chats SET title = $1 WHERE chat_id = $2",
            "Untitled Chat",
            uuid.UUID(chat_id)
        )


async def run_agent(
    pool: asyncpg.Pool,
    user_id: str,
    chat_id: str,
    user_message: str,
    background_tasks: BackgroundTasks,
    # emotion_context: dict | None = None,
    safety_flag: str | None = None,
    model_preference: str = "2" 
) -> str:

    log_meta = f"Agent runner started | chat_id: {chat_id} | user_id: {user_id}"
    if safety_flag:
        log_meta += f" | safety_flag: {safety_flag}"
    logger.info(log_meta)

    try:
        history = await load_history(pool, chat_id, background_tasks)

        if not history:
            title = await pool.fetchval("SELECT title FROM chats WHERE chat_id = $1", uuid.UUID(chat_id))
            
            # Check if it's None, empty, or default fallback
            if not title or title == "Untitled Chat":
                logger.info(f"No history or title found, generating title | chat_id: {chat_id}")
                background_tasks.add_task(get_title, pool, user_message, chat_id)
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

        result = await GRAPH.ainvoke({
            "messages": messages,
            "user_id": user_id,
            "chat_id": chat_id,
            # "emotion_context": emotion_context,
            "model_preference": model_preference,
        })

        response = result.get("response") or {}

        logger.debug(f"Persisting user and assistant messages | chat_id: {chat_id}")
        
        await save_message(
            pool, chat_id,
            role="user",
            content=user_message,
            emotional_state=response.get("emotional_state", dict()),
            safety_flag=safety_flag,
        )

        cleaned_response = (response.get("content", "")).replace("\n", "")

        await save_message(
            pool, chat_id,
            role="assistant",
            content=cleaned_response,
        )
        
        await update_chat_modify_date(pool, chat_id)
        
        logger.info(f"Agent runner completed successfully | chat_id: {chat_id}")

        return cleaned_response
        
    except Exception as e:
        logger.error(f"Agent runner failed | chat_id: {chat_id} | error: {str(e)}")
        raise
