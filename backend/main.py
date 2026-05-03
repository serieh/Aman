import os, asyncpg
from fastapi import Depends, FastAPI
from fastapi.concurrency import asynccontextmanager
from agents.runner import run_agent
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

def get_pool():
    return app.state.pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(dsn=os.getenv("CONNECTION_STRING"))
    yield

    await app.state.pool.close()

class MessageRequest(BaseModel):
    content: str

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {"msg": ";3"}


@app.post("/chat/{chat_id}/{current_user}")
async def send_message(
    chat_id: str,
    body: MessageRequest,
    # current_user = Depends(get_current_user),
    current_user: str,
    pool = Depends(get_pool),
):
    # Ownership check
    # chat = await get_chat(pool, chat_id)
    # if chat["user_id"] != current_user["user_id"]:
    #     raise HTTPException(403)

    # Safety pre-filter (run before agent)
    # flag = pre_filter(body.content)
    # if flag == "RED":
    #     return crisis_response(current_user["country"])

    reply = await run_agent(
        pool=pool,
        user_id=current_user, # current_user["user_id"]
        chat_id=chat_id,
        user_message=body.content,
    )
    return {"reply": reply}