# Temporary in-memory chat storage (replace with DB calls in Phase 1)
_chat_store: dict[str, list[dict]] = {}


def load_chat_history(chat_id) -> list[dict]:
    print(f"Loading chat history for chat_id: {chat_id}")
    # Return a copy so callers can't accidentally mutate the store
    return list(_chat_store.get(str(chat_id), []))


def save_message(chat_id, role: str, content: str) -> None:
    print(f"Saving [{role}] for chat_id: {chat_id}")
    key = str(chat_id)
    if key not in _chat_store:
        _chat_store[key] = []
    _chat_store[key].append({"role": role, "content": content})