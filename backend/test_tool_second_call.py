import asyncio
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from agent.safety.safety_runner import run_input_safety
from agent.prompts.builder import build_system_prompt
from agent.llm import groq_llm, rag_search
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.messages.tool import ToolCall

user_message = "انا بدي انتحر"
safety = run_input_safety(user_message)
system_prompt = build_system_prompt(
    safety_flag=safety.get("safety_tier"),
    mode="normal",
)

tool_call = ToolCall(name="rag_search", args={"query": "suicide hotline Jordan"}, id="call_123")
ai_msg = AIMessage(content="", tool_calls=[tool_call])

tool_output = rag_search.invoke({"query": "suicide hotline Jordan"})
tool_msg = ToolMessage(content=tool_output, tool_call_id="call_123")

msg = [SystemMessage(content=system_prompt), HumanMessage(content=user_message), ai_msg, tool_msg]
try:
    resp = groq_llm.invoke(msg)
    print("GROQ Response:", resp.content)
except Exception as e:
    print("GROQ ERROR:", e)
