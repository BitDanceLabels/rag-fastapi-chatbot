from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class CreateKnowledgeBase(BaseModel):
    name: str = Field(default=None, max_length=64)
    description: str = Field(default=None, max_length=1024)

class KnowledgeBaseResponse(CreateKnowledgeBase):
    id: UUID
    username: str
    created_at: datetime
    updated_at: datetime
