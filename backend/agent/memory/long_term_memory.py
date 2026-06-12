import uuid, asyncio, os
from qdrant_client.models import Distance, VectorParams, FilterSelector, Filter, FieldCondition, MatchValue
from langchain_core.messages import HumanMessage

from agent.config import QDRANT_USER_COLLECTION, EMBEDDINGS_VECTOR_SIZE
from agent.tools.rag.embeddings import get_embedding_model
from agent.qdrant_connection import get_shared_qdrant_client
from agent.llm import llm_fast
from logger import get_logger

logger = get_logger(__name__)


def ensure_user_collection(client, vector_size=EMBEDDINGS_VECTOR_SIZE):
    if not client.collection_exists(QDRANT_USER_COLLECTION):
        client.create_collection(
            collection_name=QDRANT_USER_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def clear_user_facts(user_id: str):
    client = get_shared_qdrant_client()
    try:
        ensure_user_collection(client)
        client.delete(
            collection_name=QDRANT_USER_COLLECTION,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id),
                        ),
                    ],
                )
            ),
        )
    except Exception as e:
        logger.error(f"Failed to clear memory: {e}")


def retrieve_user_facts(user_id: str, query: str = "") -> str:
    client = get_shared_qdrant_client()
    try:
        ensure_user_collection(client)
    except Exception:
        return ""
    
    embedder = get_embedding_model()
    
    # If no specific query, we just search for their user_id basically, 
    # but Qdrant requires a vector. We can embed a generic probe or filter.
    # We will embed the generic probe "User profile facts"
    vector = embedder.embed_query(query if query else "User profile and facts")
    
    try:
        results = client.query_points(
            collection_name=QDRANT_USER_COLLECTION,
            query=vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    ),
                ]
            ),
            limit=5
        ).points
        if not results:
            return ""
        facts = [res.payload.get("fact", "") for res in results if res.payload]
        return "\n".join(f"- {f}" for f in facts if f)
    except Exception as e:
        logger.error(f"Exception in retrieve_user_facts: {e}")
        return ""


async def extract_and_save_facts(user_id: str, new_user_message: str, ai_response: str):
    logger.info(f"Extracting new user facts for user_id: {user_id}")
    prompt = (
        "Extract any new, permanent facts about the user from the following conversation. "
        "Ignore temporary feelings or casual chat. Focus on biographical facts, persistent traits, or major events. "
        "If no new permanent facts exist, return exactly the word 'NONE'. "
        "Otherwise, return the facts as a bulleted list.\n\n"
        f"User: {new_user_message}\nAI: {ai_response}"
    )
    
    try:
        # Run in thread if llm is sync
        reply = await asyncio.to_thread(llm_fast.invoke, [HumanMessage(content=prompt)])
        content = reply.content.strip()
        
        logger.info(f"Raw reply content from llm_fast: '{content}'")
        
        if content == "NONE" or not content:
            logger.info(f"No new facts extracted for user_id: {user_id}")
            return
            
        facts = [f.strip("- ").strip() for f in content.split("\n") if f.strip("- ").strip()]
        
        if not facts:
            logger.info(f"No new facts extracted (empty list) for user_id: {user_id}")
            return
            
        logger.info(f"Extracted {len(facts)} new facts for user_id: {user_id}")
        client = get_shared_qdrant_client()
        ensure_user_collection(client)
        
        embedder = get_embedding_model()
        
        points = []
        for fact in facts:
            logger.info(f"Saving fact: '{fact}' for user_id: {user_id}")
            vec = await asyncio.to_thread(embedder.embed_query, fact)
            points.append(
                {
                    "id": str(uuid.uuid4()),
                    "vector": vec,
                    "payload": {"user_id": user_id, "fact": fact}
                }
            )
            
        client.upsert(
            collection_name=QDRANT_USER_COLLECTION,
            points=points
        )
        logger.info(f"Successfully saved {len(points)} facts to Qdrant for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to extract/save facts for user_id {user_id}: {e}")
