from .memory.controller import load_history, save_message, update_chat_modify_date
from .creator import GRAPH
from .prompts.builder import build_system_prompt
from langchain_core.messages import SystemMessage, HumanMessage
import asyncpg


SYSTEM_PROMPT = build_system_prompt()

async def run_agent(
    pool: asyncpg.Pool,
    user_id: str,
    chat_id: str,
    user_message: str,
    # emotion_context: dict | None = None,
    safety_flag: str | None = None,
) -> str:

    history = await load_history(pool, chat_id)
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT), # emotion_hint
        *history,                               
        HumanMessage(content=user_message),
    ]

    result = await GRAPH.ainvoke({
        "messages": messages,
        "user_id": user_id,
        "chat_id": chat_id,
        # "emotion_context": emotion_context,
    })

    response = result.get("response") or {}

    await save_message(
        pool, chat_id,
        role="user",
        content=user_message,
        emotional_state=response.get("emotional_state", dict()),
        safety_flag= safety_flag,
    )

    cleaned_response = (response.get("content", "")).replace("\n", " ")

    await save_message(
        pool, chat_id,
        role="assistant",
        content=cleaned_response,
    )
    await update_chat_modify_date(pool, chat_id)

    return cleaned_response