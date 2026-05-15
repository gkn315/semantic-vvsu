from fastapi import FastAPI
from pydantic import BaseModel
from agent import ask

app = FastAPI(title="Fitness Trainer Agent")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str


@app.post("/generate", response_model=ChatResponse)
async def generate(req: ChatRequest):
    return ChatResponse(response=ask(req.message))
