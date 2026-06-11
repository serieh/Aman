import asyncio
import os
import sys
import django

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from agent.llm import groq_llm, groq_with_tools
from langchain_core.messages import SystemMessage, HumanMessage

async def main():
    msg = [SystemMessage("Reply with exactly three words: 'One two three'"), HumanMessage("Go!")]
    print("--- Testing ChatGroq stream ---")
    async for chunk in groq_llm.astream(msg):
        print(f"[{chunk.content}]")
        
    print("\n--- Testing groq_with_tools stream ---")
    async for chunk in groq_with_tools.astream(msg):
        print(f"[{chunk.content}]")

asyncio.run(main())
