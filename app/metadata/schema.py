from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FileRef(BaseModel):
    file_name: str
    url: Optional[str] = None
    content_type: Optional[str] = None


class VectorData(BaseModel):
    text: Optional[list[float]] = None
    image: Optional[list[float]] = None
    ocr: Optional[list[float]] = None


class MetadataPayload(BaseModel):
    actors: List[str] = []
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    time_hint: Optional[str] = Field(
        default=None, description="Cụm thời gian mơ hồ, ví dụ: 'tháng trước', 'mấy hôm trước'"
    )
    content_type: Optional[str] = Field(
        default=None, description="chat|doc|image|ocr|other"
    )
    emotion: Optional[str] = None
    intent: Optional[str] = None
    file_refs: List[FileRef] = []
    labels: dict = {}
    vector: Optional[VectorData] = None


class MetadataItem(MetadataPayload):
    id: str
