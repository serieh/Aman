from fastapi import FastAPI
from agents.runner import run_agent

app = FastAPI()

@app.get("/")
def home():
    return {"msg": ";3"}

@app.post("/chat/{chat_id}")
async def chat(chat_id: str, message: str):
    print(f"Received chat request for chat_id: {chat_id} with message: {message}")
    reply = await run_agent(chat_id, message)
    return {"reply": reply} 