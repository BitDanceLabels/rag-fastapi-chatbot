from fastapi import APIRouter, Depends

from app.auth.dependency import AccessTokenBearer
from app.rag.schemas import (
    ChunkRequest,
    ChunkResponse,
    EmbedRequest,
    EmbedResponse,
    HybridSearchRequest,
    HybridSearchResponse,
    IngestRequest,
    IngestResponse,
    RagChatRequest,
    RagChatResponse,
    RagSearchRequest,
    RagSearchResponse,
    RechunkRequest,
    RechunkResponse,
    ReembedRequest,
    ReembedResponse,
)
from app.rag.service import RagSuperService

rag_super_router = APIRouter()
rag_super_service = RagSuperService()


@rag_super_router.post("/ingest", response_model=IngestResponse, dependencies=[Depends(AccessTokenBearer())])
async def ingest(payload: IngestRequest):
    return rag_super_service.ingest(payload)


@rag_super_router.post("/chunk", response_model=ChunkResponse, dependencies=[Depends(AccessTokenBearer())])
async def chunk(payload: ChunkRequest):
    return rag_super_service.chunk(payload)


@rag_super_router.post("/embed", response_model=EmbedResponse, dependencies=[Depends(AccessTokenBearer())])
async def embed(payload: EmbedRequest):
    return rag_super_service.embed(payload)


@rag_super_router.post("/rechunk", response_model=RechunkResponse, dependencies=[Depends(AccessTokenBearer())])
async def rechunk(payload: RechunkRequest):
    return rag_super_service.rechunk(payload)


@rag_super_router.post("/reembed", response_model=ReembedResponse, dependencies=[Depends(AccessTokenBearer())])
async def reembed(payload: ReembedRequest):
    return rag_super_service.reembed(payload)


@rag_super_router.post("/rag/search", response_model=RagSearchResponse, dependencies=[Depends(AccessTokenBearer())])
async def rag_search(payload: RagSearchRequest):
    return rag_super_service.rag_search(payload)


@rag_super_router.post(
    "/search/hybrid",
    response_model=HybridSearchResponse,
    dependencies=[Depends(AccessTokenBearer())],
)
async def hybrid_search(payload: HybridSearchRequest):
    return rag_super_service.search_hybrid(payload)


@rag_super_router.post("/rag/chat", response_model=RagChatResponse, dependencies=[Depends(AccessTokenBearer())])
async def rag_chat(payload: RagChatRequest):
    return rag_super_service.rag_chat(payload)
