def build_dynamic_context(
    language: str,
    emotion: dict | None = None,
    safety_flag: str | None = None
):
    parts = []

    parts.append(f"Conversation language: {language}")

    if emotion:
        parts.append(f"Detected emotion: {emotion}")

    if safety_flag:
        parts.append(f"Safety alert level: {safety_flag}")

    return "\n".join(parts)