import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from agent.llm import llm_fast, tools
from langchain_core.messages import SystemMessage, HumanMessage

def test_ollama_direct():
    print("Testing llm_fast.bind_tools(tools) on Mona's scenario...")
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
    
    llm_with_tools = llm_fast.bind_tools(tools)
    response = llm_with_tools.invoke(messages)
    print("\n--- RESPONSE ---")
    print("Content:", response.content)
    print("Tool Calls:", getattr(response, "tool_calls", None))
    print("--- END ---")

if __name__ == "__main__":
    test_ollama_direct()
