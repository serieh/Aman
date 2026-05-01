PROMPT_VERSION = "v1.0"

summary_prompt = ("You are summarizing part of a mental health support conversation. "
        "Write a concise summary (5-8 sentences) that captures: "
        "the user's main concerns, emotional state, and any key topics discussed. "
        "This summary will replace the original messages to save context space. "
        "Write it in third person. Be factual and empathetic.\n\n"
        f"Conversation to summarize:\n")