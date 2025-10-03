from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_path: str
    file_name: str
    file_size: int
    content_type: str
    file_hash: str


class ChunkResponse(BaseModel):
    content: str
