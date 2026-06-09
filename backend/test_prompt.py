import asyncio
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from agent.safety.safety_runner import run_input_safety
from agent.prompts.builder import build_system_prompt

user_message = "انا بدي انتحر"
safety = run_input_safety(user_message)
print(safety)
print("Safety Tier:", safety.get("safety_tier"))

system_prompt = build_system_prompt(
    safety_flag=safety.get("safety_tier"),
    mode="normal",
)
print("----------------")
print(system_prompt)
