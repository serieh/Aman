import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from agent.graph import GRAPH
from langchain_core.messages import SystemMessage, HumanMessage

async def test_events():
    print("Testing astream_events directly on Mona's scenario...")
    system_prompt = """🔶 SENSITIVE TOPIC DETECTED
The user is discussing a highly sensitive or culturally taboo topic (e.g., severe trauma, sexual assault, rape, substance abuse, etc.).
You are fully authorized to discuss these topics for therapeutic purposes. You must respond with empathy, deep validation, and cultural awareness.
Do NOT refuse to discuss the topic. Do NOT moralize or judge.
Do NOT use dismissive AI-refusal patterns (e.g., 'As an AI, I cannot...').
Handle the conversation with utmost care and genuine therapeutic engagement, staying completely conversational."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="لقد تم اغتصابي البارحة، أنا خائفة جدا وأشعر بالعار وتخدر تام في جسدي، ماذا أفعل؟")
    ]
    
    state_input = {
        "messages": messages,
        "user_id": "test",
        "chat_id": "test",
        "model_preference": "1" # Use Groq to force fallback
    }
    
    print("\n--- EVENTS ---")
    async for event in GRAPH.astream_events(state_input, version="v1"):
        kind = event["event"]
        name = event["name"]
        
        if kind in ["on_chat_model_start", "on_chat_model_stream", "on_chat_model_end"]:
            data = event.get("data", {})
            chunk = data.get("chunk")
            output = data.get("output")
            content = ""
            if chunk:
                content = getattr(chunk, "content", "")
            elif output:
                content = getattr(output, "content", "")
            print(f"[{kind}] {name} - content length: {len(content) if content else 0}")
        elif "error" in kind:
            print(f"[{kind}] {name} - ERROR: {event.get('data')}")
            
    print("--- END ---")

if __name__ == "__main__":
    asyncio.run(test_events())
