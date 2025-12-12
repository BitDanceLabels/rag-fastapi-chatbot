from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    dataset_id: str = Field(..., description="Dataset identifier (maps to knowledge base or namespace)")
    source_url: str = Field(..., description="Document source to ingest")
    topic_tags: List[str] = Field(default_factory=list)
    ocr: bool = True
    docling: bool = True
    meta: Dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    ingest_id: str
    status: str


class ChunkConfig(BaseModel):
    method: str = Field("token", description="token|sentence|page")
    max_tokens: int = 512
    overlap: int = 64


class ChunkRequest(BaseModel):
    ingest_id: str
    chunk_config: ChunkConfig


class ChunkMeta(BaseModel):
    ingest_id: str
    dataset_id: str
    topic_tags: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChunkItem(BaseModel):
    chunk_id: str
    content: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class ChunkResponse(BaseModel):
    chunks: List[ChunkItem]


class EmbedConfig(BaseModel):
    backend: str = Field("pg", description="pg|milvus|vespa|local")
    model: str = Field("llama-embed", description="Embedding model name")
    namespace: Optional[str] = None


class EmbedRequest(BaseModel):
    dataset_id: str
    chunks: List[ChunkItem]
    embed_config: EmbedConfig


class EmbedResponse(BaseModel):
    vector_ids: List[str]
    backend: str


class FilterConfig(BaseModel):
    dataset_id: str
    tags: List[str] = Field(default_factory=list)


class RechunkRequest(BaseModel):
    dataset_id: str
    tags: List[str] = Field(default_factory=list)
    chunk_config: ChunkConfig


class RechunkResponse(ChunkResponse):
    pass


class ReembedRequest(BaseModel):
    dataset_id: str
    tags: List[str] = Field(default_factory=list)
    embed_config: EmbedConfig


class ReembedResponse(EmbedResponse):
    pass


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    dataset_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    rerank: bool = False


class RagHit(BaseModel):
    chunk_id: str
    content: str
    score: float
    meta: Dict[str, Any] = Field(default_factory=dict)


class RagSearchResponse(BaseModel):
    hits: List[RagHit]


class HybridFilters(BaseModel):
    dataset_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class HybridSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    lex_k: int = 20
    vec_k: int = 20
    filters: HybridFilters = Field(default_factory=HybridFilters)
    rerank: bool = True
    rerank_top_n: int = 15
    rerank_model: str = "gpt-4o-mini"


class HybridSearchResponse(BaseModel):
    hits: List[RagHit]


class Message(BaseModel):
    role: str
    content: str


class RetrievalConfig(BaseModel):
    dataset_id: Optional[str] = None
    top_k: int = 5
    tags: List[str] = Field(default_factory=list)


class RagChatRequest(BaseModel):
    messages: List[Message]
    retrieve: bool = True
    retrieval_config: Optional[RetrievalConfig] = None


class RagChatResponse(BaseModel):
    answer: str
    sources: List[RagHit] = Field(default_factory=list)
