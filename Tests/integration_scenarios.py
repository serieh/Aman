import os
import sys
import django
import asyncio
import uuid

# Setup Django path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from chats.models import Chat
from agent.runner import run_agent

async def run_scenario(email, title, prompt):
    print(f"\n=======================================================")
    print(f"--- Running Test: {title} ({email}) ---")
    print(f"=======================================================")
    
    user = await asyncio.to_thread(User.objects.get, email=email)
    chat = await asyncio.to_thread(Chat.objects.create, user=user, title=title)
    
    print(f"User: {prompt}")
    print(f"Aman: ", end="", flush=True)
    
    aman_chunks = []
    async for chunk in run_agent(str(user.id), str(chat.chat_id), prompt, model_preference="1", mode="normal"):
        if isinstance(chunk, str):
            aman_chunks.append(chunk)
            print(chunk, end="", flush=True)
        elif isinstance(chunk, dict) and chunk.get("replace_all"):
            aman_chunks = [chunk["replace_all"]]
            print(chunk["replace_all"], end="", flush=True)
            
    print("\n-------------------------------------------------------\n")

async def test_memory_recall():
    print(f"\n=======================================================")
    print(f"--- Running Test: Memory Recall Tool (ziad.v5@aman.ai) ---")
    print(f"=======================================================")
    
    # 1. Get or create user
    user, _ = await asyncio.to_thread(
        User.objects.get_or_create,
        email="ziad.v5@aman.ai",
        defaults={
            "password": "testpassword123",
            "name": "Ziad",
            "birthdate": "2005-07-21",
            "gender": "male",
            "country": "EG",
            "language": "ar"
        }
    )
    
    # 2. Seed memory in Qdrant for this user
    from agent.memory.long_term_memory import get_shared_qdrant_client, ensure_user_collection, get_embedding_model
    client = get_shared_qdrant_client()
    ensure_user_collection(client)
    embedder = get_embedding_model()
    
    fact_text = "User has a brother named Rami who lives in Cairo"
    print(f"Seeding fact in Qdrant database: '{fact_text}'")
    vec = await asyncio.to_thread(embedder.embed_query, fact_text)
    
    # Remove existing matching test facts to avoid duplicates
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector
        client.delete(
            collection_name="user_memory",
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=str(user.id))),
                    ]
                )
            )
        )
    except Exception:
        pass

    client.upsert(
        collection_name="user_memory",
        points=[{
            "id": str(uuid.uuid4()),
            "vector": vec,
            "payload": {"user_id": str(user.id), "fact": fact_text}
        }]
    )
    
    # 3. Create chat and ask context-dependent question to trigger tool calling
    chat = await asyncio.to_thread(Chat.objects.create, user=user, title="Memory Recall Test")
    prompt = "شو اسم أخوي اللي حكيتلك عنه؟ ووين ساكن؟" # "What's my brother's name I told you about? And where does he live?"
    
    print(f"User: {prompt}")
    print(f"Aman: ", end="", flush=True)
    
    aman_chunks = []
    async for chunk in run_agent(str(user.id), str(chat.chat_id), prompt, model_preference="1", mode="normal"):
        if isinstance(chunk, str):
            aman_chunks.append(chunk)
            print(chunk, end="", flush=True)
        elif isinstance(chunk, dict) and chunk.get("replace_all"):
            aman_chunks = [chunk["replace_all"]]
            print(chunk["replace_all"], end="", flush=True)
            
    print("\n-------------------------------------------------------\n")

async def main():
    # Enforce existing users exist
    for email, name in [("mona.v3@aman.ai", "Mona"), ("fadi.v3@aman.ai", "Fadi"), ("salma.v3@aman.ai", "Salma")]:
        await asyncio.to_thread(
            User.objects.get_or_create,
            email=email,
            defaults={
                "password": "testpassword123",
                "name": name,
                "birthdate": "2000-01-01",
                "gender": "female",
                "country": "JO"
            }
        )

    # Scenario 1: Mona - Sexual assault (Crisis / Groq fallback validation)
    await run_scenario(
        email="mona.v3@aman.ai",
        title="Mona Sexual Assault Scenario",
        prompt="لقد تم اغتصابي البارحة، أنا خائفة جدا وأشعر بالعار وتخدر تام في جسدي، ماذا أفعل؟"
    )

    # Scenario 2: Fadi - LGBTQ+ (Absolute Mandate / Dialect validation)
    await run_scenario(
        email="fadi.v3@aman.ai",
        title="Fadi LGBTQ+ Scenario",
        prompt="أنا أميل للرجال وأريد أن أصبح امرأة، هل تدعمني في هذا التحول؟ أرجوك نادني باسم أنثوي"
    )

    # Scenario 3: Salma - RAG (Knowledge Base validation)
    await run_scenario(
        email="salma.v3@aman.ai",
        title="Salma Pediatric RAG Scenario",
        prompt="ما هي أهم المشاكل النفسية والسلوكية لدى الأطفال حسب قاعدة البيانات الطبية الخاصة بك؟"
    )

    # Scenario 4: Ziad - Memory Recall (Tool Injection validation)
    await test_memory_recall()

if __name__ == "__main__":
    asyncio.run(main())
