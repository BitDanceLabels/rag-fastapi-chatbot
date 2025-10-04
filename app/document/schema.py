from pydantic import BaseModel
from uuid import UUID

class UploadResponse(BaseModel):
    object_path: str
    file_name: str
    file_size: int
    content_type: str
    file_hash: str


class ChunkResponse(BaseModel):
    id: UUID
    content: str


