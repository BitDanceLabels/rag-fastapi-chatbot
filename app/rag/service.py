from __future__ import annotations

import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import HTTPException

from app.config import Config
from app.rag.schemas import (
    ChunkConfig,
    ChunkItem,
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
    RagHit,
    RagSearchRequest,
    RagSearchResponse,
    RechunkRequest,
    RechunkResponse,
    ReembedRequest,
    ReembedResponse,
)


class RagSuperService:
    """
    Lightweight, in-memory RAG pipeline for the RAG Super system.
    Replace with real storage (MinIO/PGVector/Vespa) as needed.
    """

    def __init__(self) -> None:
        self.ingests: Dict[str, dict] = {}
        self.dataset_chunks: Dict[str, List[ChunkItem]] = {}
        self.vector_backend = Config.VECTOR_BACKEND or "pg"
        self.default_lex_k = Config.HYBRID_LEX_K
        self.default_vec_k = Config.HYBRID_VEC_K
        self.default_rerank_top_n = Config.RERANK_TOP_N
        self.default_rerank_model = Config.RERANK_MODEL

    # Ingest
    def ingest(self, payload: IngestRequest) -> IngestResponse:
        ingest_id = f"ing-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        self.ingests[ingest_id] = {
            "dataset_id": payload.dataset_id,
            "source_url": payload.source_url,
            "topic_tags": payload.topic_tags,
            "ocr": payload.ocr,
            "docling": payload.docling,
            "meta": payload.meta,
            "status": "queued",
            "created_at": now,
        }
        return IngestResponse(ingest_id=ingest_id, status="queued")

    # Chunk
    def chunk(self, payload: ChunkRequest) -> ChunkResponse:
        ingest = self.ingests.get(payload.ingest_id)
        if not ingest:
            raise HTTPException(status_code=404, detail="Ingest not found")

        base_text = ingest["meta"].get(
            "title", f"Tài liệu từ {ingest['source_url']} thuộc dataset {ingest['dataset_id']}"
        )
        chunk_items = self._generate_chunks(
            base_text=base_text,
            ingest_id=payload.ingest_id,
            dataset_id=ingest["dataset_id"],
            tags=ingest["topic_tags"],
            source_url=ingest["source_url"],
            chunk_config=payload.chunk_config,
        )
        self.dataset_chunks.setdefault(ingest["dataset_id"], [])
        self.dataset_chunks[ingest["dataset_id"]].extend(chunk_items)
        ingest["status"] = "chunked"
        return ChunkResponse(chunks=chunk_items)

    # Embed
    def embed(self, payload: EmbedRequest) -> EmbedResponse:
        if not payload.chunks:
            raise HTTPException(status_code=400, detail="No chunks provided for embedding")
        backend = payload.embed_config.backend or self.vector_backend
        vector_ids = [chunk.chunk_id for chunk in payload.chunks]
        # In a real system, write vectors to PGVector/Vespa/Milvus here
        return EmbedResponse(vector_ids=vector_ids, backend=backend)

    # Rechunk / Reembed
    def rechunk(self, payload: RechunkRequest) -> RechunkResponse:
        ingest_id = self._select_ingest_for_dataset(payload.dataset_id, payload.tags)
        if not ingest_id:
            ingest_id = self.ingest(
                IngestRequest(
                    dataset_id=payload.dataset_id,
                    source_url="rerun://local",
                    topic_tags=payload.tags,
                    ocr=True,
                    docling=True,
                    meta={"note": "Auto-ingest for rechunk"},
                )
            ).ingest_id
        chunk_response = self.chunk(
            ChunkRequest(ingest_id=ingest_id, chunk_config=payload.chunk_config)
        )
        return RechunkResponse(chunks=chunk_response.chunks)

    def reembed(self, payload: ReembedRequest) -> ReembedResponse:
        chunks = self.dataset_chunks.get(payload.dataset_id, [])
        if not chunks:
            raise HTTPException(status_code=404, detail="No chunks found for dataset to re-embed")
        backend = payload.embed_config.backend or self.vector_backend
        vector_ids = [c.chunk_id for c in chunks]
        return ReembedResponse(vector_ids=vector_ids, backend=backend)

    # Search
    def rag_search(self, payload: RagSearchRequest) -> RagSearchResponse:
        candidates = self._get_candidates(payload.dataset_id, payload.tags)
        hits = []
        for chunk in candidates:
            score = self._text_score(payload.query, chunk.content)
            hits.append(
                RagHit(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    score=score,
                    meta=chunk.meta,
                )
            )

        hits = sorted(hits, key=lambda h: h.score, reverse=True)[: payload.top_k]
        if payload.rerank:
            hits = self._rerank(hits, top_n=len(hits))
        return RagSearchResponse(hits=hits)

    def search_hybrid(self, payload: HybridSearchRequest) -> HybridSearchResponse:
        candidates = self._get_candidates(payload.filters.dataset_id, payload.filters.tags)
        lex_k = payload.lex_k or self.default_lex_k
        vec_k = payload.vec_k or self.default_vec_k
        top_k = payload.top_k

        lex_hits = sorted(
            (self._lexical_hit(payload.query, c) for c in candidates),
            key=lambda h: h.score,
            reverse=True,
        )[:lex_k]

        vec_hits = sorted(
            (self._vector_hit(payload.query, c) for c in candidates),
            key=lambda h: h.score,
            reverse=True,
        )[:vec_k]

        merged: Dict[str, RagHit] = {}
        for hit in lex_hits + vec_hits:
            if hit.chunk_id in merged:
                # Simple merge: average the scores to simulate fusion
                merged[hit.chunk_id].score = (merged[hit.chunk_id].score + hit.score) / 2
            else:
                merged[hit.chunk_id] = hit

        merged_hits = sorted(merged.values(), key=lambda h: h.score, reverse=True)
        rerank_top_n = payload.rerank_top_n or self.default_rerank_top_n
        if payload.rerank:
            merged_hits = self._rerank(merged_hits[:rerank_top_n], top_n=rerank_top_n)
        final_hits = merged_hits[:top_k]
        return HybridSearchResponse(hits=final_hits)

    # Chat
    def rag_chat(self, payload: RagChatRequest) -> RagChatResponse:
        user_msg = next((m for m in reversed(payload.messages) if m.role == "user"), None)
        user_text = user_msg.content if user_msg else ""
        sources: List[RagHit] = []
        if payload.retrieve and payload.retrieval_config:
            search_hits = self.rag_search(
                RagSearchRequest(
                    query=user_text,
                    top_k=payload.retrieval_config.top_k,
                    dataset_id=payload.retrieval_config.dataset_id,
                    tags=payload.retrieval_config.tags,
                    rerank=False,
                )
            )
            sources = search_hits.hits

        answer = (
            f"Tóm tắt nhanh: {user_text}. "
            f"Đã dùng {len(sources)} nguồn tham chiếu từ RAG pipeline."
        )
        return RagChatResponse(answer=answer, sources=sources)

    # Helpers
    def _generate_chunks(
        self,
        base_text: str,
        ingest_id: str,
        dataset_id: str,
        tags: List[str],
        source_url: str,
        chunk_config: ChunkConfig,
    ) -> List[ChunkItem]:
        slices = [
            f"{base_text} (phần 1, method={chunk_config.method}, max_tokens={chunk_config.max_tokens})",
            f"{base_text} (phần 2, overlap={chunk_config.overlap})",
            f"{base_text} (phần 3, topic_tags={','.join(tags) if tags else 'none'})",
        ]
        chunk_items = []
        for text in slices:
            chunk_id = f"c-{uuid.uuid4().hex[:8]}"
            meta = {
                "ingest_id": ingest_id,
                "dataset_id": dataset_id,
                "tags": tags,
                "source_url": source_url,
                "chunk_config": chunk_config.model_dump(),
            }
            chunk_items.append(ChunkItem(chunk_id=chunk_id, content=text, meta=meta))
        return chunk_items

    def _select_ingest_for_dataset(self, dataset_id: str, tags: List[str]) -> Optional[str]:
        for ingest_id, ingest in self.ingests.items():
            if ingest["dataset_id"] == dataset_id:
                if not tags or any(t in ingest["topic_tags"] for t in tags):
                    return ingest_id
        return None

    def _get_candidates(self, dataset_id: Optional[str], tags: List[str]) -> List[ChunkItem]:
        all_chunks: List[ChunkItem] = []
        if dataset_id:
            all_chunks.extend(self.dataset_chunks.get(dataset_id, []))
        else:
            for chunks in self.dataset_chunks.values():
                all_chunks.extend(chunks)

        if tags:
            filtered = []
            for chunk in all_chunks:
                chunk_tags = chunk.meta.get("tags", [])
                if any(t in chunk_tags for t in tags):
                    filtered.append(chunk)
            return filtered
        return all_chunks

    def _text_score(self, query: str, content: str) -> float:
        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())
        overlap = query_terms.intersection(content_terms)
        if not content_terms:
            return 0.0
        return round(len(overlap) / max(len(query_terms), 1), 3)

    def _lexical_hit(self, query: str, chunk: ChunkItem) -> RagHit:
        score = self._text_score(query, chunk.content) + random.uniform(0.01, 0.05)
        return RagHit(chunk_id=chunk.chunk_id, content=chunk.content, score=score, meta=chunk.meta)

    def _vector_hit(self, query: str, chunk: ChunkItem) -> RagHit:
        # Simulate vector similarity with a deterministic fallback
        base = self._text_score(query, chunk.content)
        jitter = random.uniform(0.02, 0.06)
        score = round(min(base + jitter + 0.4, 1.0), 3)
        return RagHit(chunk_id=chunk.chunk_id, content=chunk.content, score=score, meta=chunk.meta)

    def _rerank(self, hits: List[RagHit], top_n: int) -> List[RagHit]:
        reranked = []
        for idx, hit in enumerate(hits[:top_n]):
            boost = max(0.0, (top_n - idx) * 0.001)
            reranked.append(
                RagHit(
                    chunk_id=hit.chunk_id,
                    content=hit.content,
                    score=round(min(hit.score + boost, 1.0), 3),
                    meta=hit.meta,
                )
            )
        return reranked
