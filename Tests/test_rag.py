import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from chats.models import Chat
from agent.runner import run_agent

async def test_case(email, scenario):
    user = await asyncio.to_thread(User.objects.get, email=email)
    chat = await asyncio.to_thread(Chat.objects.create, user=user, title="RAG Test")
    
    print(f"\n--- Testing {email} ---")
    print(f"User: {scenario}")
    print(f"Aman: ", end="", flush=True)
    
    async for chunk in run_agent(str(user.id), str(chat.chat_id), scenario, model_preference="1", mode="normal"):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
        elif isinstance(chunk, dict) and chunk.get("replace_all"):
            print(chunk["replace_all"])
            
    print("\n--- End Test ---\n")

if __name__ == "__main__":
    asyncio.run(test_case("salma.v3@aman.ai", "ما هي أهم المشاكل النفسية والسلوكية لدى الأطفال حسب قاعدة البيانات الطبية الخاصة بك؟"))
