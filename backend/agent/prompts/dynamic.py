def build_dynamic_context(
    language: str,
    emotion: dict | None = None,
    safety_flag: str | None = None
):
    parts = []

    parts.append(f"Conversation language: {language}")

    if emotion and isinstance(emotion, dict):
        # Format top emotions from ML classifier output
        # e.g. {"sadness": 0.72, "fear": 0.41, ...}
        top_emotions = sorted(emotion.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_emotions:
            formatted = ", ".join(f"{name}={score:.0%}" for name, score in top_emotions)
            parts.append(f"Detected emotions (ML model): {formatted}")

    if safety_flag:
        parts.append(f"Safety alert level: {safety_flag}")

    return "\n".join(parts)