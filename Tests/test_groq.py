import asyncio
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from agent.llm import groq_llm
from langchain_core.messages import SystemMessage, HumanMessage

msg = [SystemMessage("Hello"), HumanMessage("انا بدي انتحر")]
try:
    resp = groq_llm.invoke(msg)
    print("GROQ Response:", resp.content)
except Exception as e:
    print("GROQ ERROR:", e)
