from fastapi import FastAPI
from agents.runner import run_chat

app = FastAPI()

@app.get("/")
def home():
    return {"msg": ";3"}

@app.post("/chat/{chat_id}")
def chat(chat_id: int, message: str):
    print(f"Received chat request for chat_id: {chat_id} with message: {message}")
    reply = run_chat(chat_id, message)
    return {"reply": reply} 