import os
import sys
import django
import asyncio

# Setup Django path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from agent.memory.long_term_memory import extract_and_save_facts, retrieve_user_facts, clear_user_facts

async def test_saving_and_retrieving():
    print("=========================================")
    print("Testing Long Term Memory Saving & Retrieval")
    print("=========================================")
    
    # 1. Get or create test user
    user, _ = await asyncio.to_thread(
        User.objects.get_or_create,
        email="memory_test@aman.ai",
        defaults={
            "password": "testpassword123",
            "name": "Memory Test User",
            "birthdate": "1999-09-09",
            "gender": "male",
            "country": "JO"
        }
    )
    user_id_str = str(user.id)
    
    # 2. Clear existing facts to start fresh
    print("Clearing existing facts for test user...")
    clear_user_facts(user_id_str)
    
    # 3. Simulate message that contains a clear permanent fact
    user_message = "I just got a new job as a software developer at Google today!"
    ai_response = "Congratulations! That is amazing news. You must be really proud."
    
    print(f"User message: {user_message}")
    print(f"AI response: {ai_response}")
    print("Extracting and saving facts...")
    
    # Await the saving task directly
    await extract_and_save_facts(user_id_str, user_message, ai_response)
    
    # 4. Attempt retrieval
    print("Retrieving saved facts from Qdrant...")
    retrieved = retrieve_user_facts(user_id_str, query="job or employment")
    
    print("\n-----------------------------------------")
    print("Retrieved facts:")
    print(retrieved if retrieved else "[No facts retrieved]")
    print("-----------------------------------------\n")
    
    if retrieved and "job" in retrieved.lower() or "google" in retrieved.lower():
        print("Success! Fact was correctly extracted, embedded, saved, and retrieved.")
    else:
        print("Failure: Expected fact was not retrieved.")

if __name__ == "__main__":
    asyncio.run(test_saving_and_retrieving())
