from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    chat_id: str = Field(..., description="Chat session id (UUID)")
    question: str = Field(..., description="User question")
