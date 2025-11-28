from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FileRef(BaseModel):
    file_name: str
    url: Optional[str] = None
    content_type: Optional[str] = None


class Metadata(BaseModel):
    actors: List[str] = []
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    content_type: Optional[str] = None
    emotion: Optional[str] = None
    intent: Optional[str] = None
    file_refs: List[FileRef] = []


class VectorInfo(BaseModel):
    text_score: float
    image_score: Optional[float] = None
    ocr_score: Optional[float] = None


class SearchPlusRequest(BaseModel):
    query: str = Field(..., description="User query")
    actors: List[str] = []
    time_hint: Optional[str] = None
    content_types: List[str] = []
    file_types: List[str] = []
    mode: str = Field("rag", description="rag|exact")


class SearchPlusItem(BaseModel):
    id: str
    snippet: str
    metadata: Metadata
    vector: VectorInfo


class SearchPlusResponse(BaseModel):
    parsed_time: Optional[dict] = None
    items: List[SearchPlusItem] = []
