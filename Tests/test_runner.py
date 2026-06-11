import os
import django
import sys
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from agent.runner import run_agent, run_agent_async
from users.models import User
from chats.models import Chat

from asgiref.sync import sync_to_async

@sync_to_async
def get_user_and_chat():
    user = User.objects.first()
    if not user:
        return None, None
    chat = Chat.objects.create(user=user, title="Test Tool Execution")
    return user, chat

async def main():
    user, chat = await get_user_and_chat()
    if not user:
        print("No users found.")
        return
    
    print(f"Testing with User: {user.name}, Chat ID: {chat.chat_id}")
    
    print("\n--- ASYNC STREAM ---")
    async for chunk in run_agent_async(str(user.id), str(chat.chat_id), "I feel anxious. What does the RAG knowledge base say about coping strategies?", model_preference="1"):
        print(chunk, end="", flush=True)
    print("\n--------------------")

if __name__ == "__main__":
    asyncio.run(main())
