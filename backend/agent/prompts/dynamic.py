from __future__ import annotations


# ── Emotion-to-instruction mappings ──────────────────────────────────────────

_EMOTION_INSTRUCTIONS: dict[str, str] = {
    "sadness": (
        "The user is expressing sadness. Use empathetic, validating language. "
        "Reflect their feelings back gently. Avoid rushing to solutions."
    ),
    "grief": (
        "The user is experiencing grief. Hold space for their pain. "
        "Do not minimize or rush the grieving process. Witness their experience."
    ),
    "anger": (
        "The user is expressing anger. Acknowledge their frustration without "
        "escalating. Do not be dismissive or preachy. Validate the feeling first."
    ),
    "fear": (
        "The user is expressing fear. Provide reassurance and normalize their "
        "anxiety. Help ground them without minimizing the concern."
    ),
    "nervousness": (
        "The user is feeling nervous or anxious. Use a calm, steady tone. "
        "Help normalize the feeling and gently explore the source."
    ),
    "disgust": (
        "The user is expressing disgust. Acknowledge the feeling without judgment. "
        "Explore what triggered it with curiosity, not confrontation."
    ),
    "confusion": (
        "The user seems confused. Be clear and structured in your response. "
        "Ask clarifying questions if needed. Break things down step by step."
    ),
    "embarrassment": (
        "The user feels embarrassed. Normalize their experience. "
        "Reassure them there is no judgment. Be warm and non-evaluative."
    ),
    "remorse": (
        "The user is feeling remorse or guilt. Acknowledge the weight of that feeling. "
        "Gently explore without reinforcing self-blame."
    ),
    "disappointment": (
        "The user is disappointed. Validate the gap between expectation and reality. "
        "Be present with them without immediately problem-solving."
    ),
    "love": (
        "The user is expressing love or affection. Respond warmly. "
        "Support and affirm the positive emotion."
    ),
    "gratitude": (
        "The user is expressing gratitude. Receive it warmly and affirm the connection."
    ),
    "optimism": (
        "The user is feeling hopeful. Encourage and support the optimism "
        "while staying grounded and realistic."
    ),
    "caring": (
        "The user is showing care for someone. Acknowledge their compassion. "
        "Explore the situation they're caring about."
    ),
    "joy": (
        "The user is expressing happiness. Share in the positive moment. "
        "Be warm and celebratory where appropriate."
    ),
}

# ── Safety tier instructions ─────────────────────────────────────────────────

_SAFETY_TIER_INSTRUCTIONS: dict[str, str] = {
    "RED": (
        "⚠️ CRISIS DETECTED — HIGHEST PRIORITY ⚠️\n"
        "The user may be in immediate danger (suicidal ideation, self-harm, or harm to others).\n"
        "1) STOP normal conversation immediately.\n"
        "2) Respond calmly, directly, and with compassion.\n"
        "3) Ask if they are safe right now.\n"
        "4) Do NOT use guilt, shame, moral judgment, or dismissive language.\n"
        "5) Do NOT provide hotline numbers or emergency numbers.\n"
        "6) Do NOT use routing scripts (e.g. 'find someone you trust').\n"
        "7) Stay present. Listen. Be the sanctuary."
    ),
    "GRAY": (
        "🔶 SENSITIVE TOPIC DETECTED\n"
        "The user is discussing a culturally sensitive topic. "
        "Respond with empathy and cultural awareness. "
        "Do NOT refuse to discuss the topic. Do NOT moralize or judge. "
        "Do NOT use dismissive AI-refusal patterns. "
        "Handle with care and genuine therapeutic engagement."
    ),
}


def _build_emotion_block(emotion: dict) -> str:
    """Build contextual instructions from the top detected emotions."""
    if not emotion or not isinstance(emotion, dict):
        return ""

    top_emotions = sorted(emotion.items(), key=lambda x: x[1], reverse=True)[:3]
    if not top_emotions:
        return ""

    parts = []

    # Raw scores for the LLM's awareness
    formatted_scores = ", ".join(f"{name}={score:.0%}" for name, score in top_emotions)
    parts.append(f"Detected emotions (ML model): {formatted_scores}")

    # Contextual behavioral instructions for the dominant emotion(s)
    instructions = []
    for name, score in top_emotions:
        if score >= 0.20 and name in _EMOTION_INSTRUCTIONS:
            instructions.append(_EMOTION_INSTRUCTIONS[name])

    if instructions:
        parts.append("Emotion-aware response guidance:")
        parts.extend(f"  • {inst}" for inst in instructions)

    return "\n".join(parts)


def _build_safety_block(
    safety_flag: str | None,
    grey_area_categories: str = "",
) -> str:
    """Build contextual instructions from safety tier and grey-area categories."""
    if not safety_flag and not grey_area_categories:
        return ""

    parts = []

    if safety_flag and safety_flag in _SAFETY_TIER_INSTRUCTIONS:
        parts.append(_SAFETY_TIER_INSTRUCTIONS[safety_flag])

    if grey_area_categories:
        parts.append(
            f"Detected sensitive topic(s): {grey_area_categories}\n"
            "Respond with cultural sensitivity and empathy. "
            "Do not refuse to discuss, but handle with care."
        )

    return "\n".join(parts)


def build_dynamic_context(
    language: str,
    emotion: dict | None = None,
    safety_flag: str | None = None,
    grey_area_categories: str = "",
) -> str:
    """
    Combine emotion estimation and safety detection into a single
    dynamic context block injected into the system prompt per-message.

    The combined context ensures the LLM's tone, empathy level, and
    topic handling are all adapted to the user's current emotional
    state AND any safety/sensitivity signals detected.
    """
    sections = []

    sections.append(f"Conversation language: {language}")

    # Safety context (highest priority — goes first)
    safety_block = _build_safety_block(safety_flag, grey_area_categories)
    if safety_block:
        sections.append(safety_block)

    # Emotion context (influences tone and approach)
    emotion_block = _build_emotion_block(emotion)
    if emotion_block:
        sections.append(emotion_block)

    # Combined guidance when BOTH safety + strong emotion are present
    if safety_flag and emotion and isinstance(emotion, dict):
        top_emotion = max(emotion.items(), key=lambda x: x[1], default=(None, 0))
        if top_emotion[0] and top_emotion[1] >= 0.30:
            emotion_name = top_emotion[0]
            if safety_flag == "RED":
                sections.append(
                    f"Combined context: The user shows strong {emotion_name} ({top_emotion[1]:.0%}) "
                    f"alongside a crisis signal. Adapt your crisis response to acknowledge "
                    f"the {emotion_name} while maintaining safety-first protocol."
                )
            elif safety_flag == "GRAY":
                sections.append(
                    f"Combined context: The user shows strong {emotion_name} ({top_emotion[1]:.0%}) "
                    f"while discussing a sensitive topic. Let the emotional tone guide your "
                    f"empathy level — this isn't just an intellectual question, it's emotionally charged."
                )

    return "\n\n".join(sections)