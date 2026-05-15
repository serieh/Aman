import os, asyncpg
from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from fastapi.concurrency import asynccontextmanager
from agents.runner import run_agent
from dotenv import load_dotenv
from pydantic import BaseModel
from logger import get_logger

logger = get_logger(__name__)

logger.info("Starting application...")
load_dotenv()

def get_pool():
    logger.info("Getting database connection pool...")
    return app.state.pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Aman application lifecycle...")
    try:
        app.state.pool = await asyncpg.create_pool(dsn=os.getenv("CONNECTION_STRING"))
        logger.info("Database connection pool initialized successfully.")
        yield
    except Exception as e:
        # ADDED LOG: Critical system health tracking
        logger.error(f"Failed to initialize database pool: {e}")
        raise
    finally:
        if hasattr(app.state, 'pool'):
            await app.state.pool.close()
            logger.info("Database connection pool closed.")

class MessageRequest(BaseModel):
    content: str

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    logger.info("Home endpoint accessed.")
    return {"msg": ";3"}


@app.post("/chat/{chat_id}/{current_user}/{model_preference}")
async def send_message(
    chat_id: str,
    body: MessageRequest,
    # current_user = Depends(get_current_user),
    current_user: str,
    background_tasks: BackgroundTasks,
    model_preference:str = "1",
    pool = Depends(get_pool),
):
    logger.info(f"Chat execution started | chat_id: {chat_id} | user_id: {current_user} | model_preference: {model_preference}")
    # chat = await get_chat(pool, chat_id)
    # if chat["user_id"] != current_user["user_id"]:
    #     raise HTTPException(403)

    # Safety pre-filter (run before agent)
    # flag = pre_filter(body.content)
    # if flag == "RED":
    #     return crisis_response(current_user["country"])
    try:
        logger.debug(f"Passing context to LangGraph agent | chat_id: {chat_id}") 
        reply = await run_agent(
            pool=pool,
            user_id=current_user,
            chat_id=chat_id,
            user_message=body.content,
            background_tasks=background_tasks,
            model_preference=model_preference
        )
        logger.info(f"Agent execution completed | chat_id: {chat_id}")
        return {"reply": reply}
            
    except Exception as e:
        logger.error(f"Agent execution failed | chat_id: {chat_id} | error: {str(e)}")
        raise HTTPException(status_code=500, detail="Aman encountered an internal error.")