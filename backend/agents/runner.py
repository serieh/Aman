from .memory import load_chat_history, save_message
from .creator import AgentCreator

agent = AgentCreator()

def run_chat(chat_id: int | str, user_message: str) -> str:
    print(f"Running chat for chat_id: {chat_id} with message: {user_message}")

    # Load existing history and append the new user message
    history = load_chat_history(chat_id)
    history.append({"role": "user", "content": user_message})
    

    # Get reply (history is passed directly — no double-wrapping)
    reply = agent.chat(history)  # ← single dict, not history list

    # Persist both sides
    save_message(chat_id, "user", user_message)
    save_message(chat_id, "assistant", reply)

    return reply    