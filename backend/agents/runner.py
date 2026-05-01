from .memory import get_history_for_agent, save_message
from .creator import AgentCreator
from .prompts.builder import build_system_prompt
from langchain_core.messages import SystemMessage, HumanMessage

agent = AgentCreator()

async def run_agent(chat_id: str, user_input: str):
    history = await get_history_for_agent(chat_id, agent)

    # system_prompt = build_system_prompt()

    messages = [
        # SystemMessage(content=system_prompt),
        *history,
        HumanMessage(content=user_input),
    ]

    save_message(chat_id, "user", user_input)

    reply = await agent.chat(messages)

    save_message(chat_id, "assistant", reply)

    return reply