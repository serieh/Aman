import asyncio
import os
import sys
import django

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from agent.safety.safety_runner import run_input_safety
from agent.prompts.builder import build_system_prompt
from agent.graph import GRAPH
from langchain_core.messages import SystemMessage, HumanMessage

async def main():
    user_message = "انا بدي انتحر"
    system_prompt = "Reply strictly with three words: One two three"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    
    state_input = {
        "messages": messages,
        "user_id": "test_user",
        "chat_id": "test_chat",
        "model_preference": "1"
    }
    
    print("--- Testing GRAPH astream_events ---")
    async for event in GRAPH.astream_events(state_input, version="v1"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            name = event["name"]
            print(f"[{name}] chunk_content: {repr(chunk.content)}")

asyncio.run(main())
