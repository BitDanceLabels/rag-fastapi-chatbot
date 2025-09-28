from fastapi import FastAPI
from app.llm_model.routes import chat_router

# Initialize FastAPI app
app = FastAPI(title="Chat API with Streaming")

app.include_router(chat_router, prefix=f"/api/v1/chat", tags=["chat"])
