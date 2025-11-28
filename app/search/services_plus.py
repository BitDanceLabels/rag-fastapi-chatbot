from __future__ import annotations

import uuid
from typing import List

from app.search.time_parser import parse_time_hint
from app.search.schema_plus import (
    SearchPlusRequest,
    SearchPlusResponse,
    SearchPlusItem,
    Metadata,
    FileRef,
    VectorInfo,
)
from app.metadata.store import metadata_store


class SearchPlusService:
    """
    Stub service: parse filters, mock retrieval.
    Replace mock_items with actual vector search (text/image/ocr) + metadata filters.
    """

    def search(self, payload: SearchPlusRequest) -> SearchPlusResponse:
        parsed_time = None
        time_range = parse_time_hint(payload.time_hint)
        if time_range:
            parsed_time = {
                "start": time_range[0].isoformat(),
                "end": time_range[1].isoformat(),
            }

        # Build results from metadata store (simple filter demo)
        mock_items: List[SearchPlusItem] = []
        for item in metadata_store.all():
            # Filter by actors (if provided)
            if payload.actors:
                if not any(a in item.actors for a in payload.actors):
                    continue
            # Filter by content_type (if provided)
            if payload.content_types:
                if item.content_type not in payload.content_types:
                    continue
            # Filter by time range hint overlap
            if time_range and item.time_start and item.time_end:
                start, end = time_range
                if item.time_end < start or item.time_start > end:
                    continue

            mock_items.append(
                SearchPlusItem(
                    id=item.id,
                    snippet=f"Kết quả khớp: {payload.query}",
                    metadata=Metadata(
                        actors=item.actors,
                        time_start=item.time_start,
                        time_end=item.time_end,
                        content_type=item.content_type,
                        emotion=item.emotion,
                        intent=item.intent,
                        file_refs=[FileRef(**ref.dict()) for ref in item.file_refs],
                    ),
                    vector=VectorInfo(text_score=0.8, image_score=0.0, ocr_score=0.0),
                )
            )

        # If no item matched, fall back to one mock item to show structure
        if not mock_items:
            mock_items = [
                SearchPlusItem(
                    id=str(uuid.uuid4()),
                    snippet="Đoạn chat/summary khớp câu hỏi: " + payload.query,
                    metadata=Metadata(
                        actors=payload.actors or ["demo-actor"],
                        time_start=time_range[0] if time_range else None,
                        time_end=time_range[1] if time_range else None,
                        content_type=(payload.content_types[0] if payload.content_types else "chat"),
                        emotion="neutral",
                        intent="search",
                        file_refs=[
                            FileRef(
                                file_name="chatbot.csv",
                                url="minio://friendifyai/tmp/chatbot.csv",
                                content_type="text/csv",
                            )
                        ],
                    ),
                    vector=VectorInfo(text_score=0.82, image_score=0.0, ocr_score=0.0),
                )
            ]

        return SearchPlusResponse(parsed_time=parsed_time, items=mock_items)
