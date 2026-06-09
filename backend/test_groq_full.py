import asyncio
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from agent.safety.safety_runner import run_input_safety
from agent.prompts.builder import build_system_prompt
from agent.llm import groq_llm
from langchain_core.messages import SystemMessage, HumanMessage

user_message = "انا بدي انتحر"
safety = run_input_safety(user_message)
system_prompt = build_system_prompt(
    safety_flag=safety.get("safety_tier"),
    mode="normal",
)

msg = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
try:
    resp = groq_llm.invoke(msg)
    print("GROQ Response:", resp.content)
except Exception as e:
    print("GROQ ERROR:", e)
