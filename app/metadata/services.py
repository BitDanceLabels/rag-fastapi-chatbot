from __future__ import annotations

import uuid
from datetime import datetime

from app.metadata.schema import MetadataPayload, MetadataItem
from app.metadata.store import metadata_store
from app.search.time_parser import parse_time_hint


class MetadataService:
    def upsert(self, payload: MetadataPayload, item_id: str | None = None) -> MetadataItem:
        # Resolve time hint
        time_start = payload.time_start
        time_end = payload.time_end
        if payload.time_hint and not (time_start and time_end):
            parsed = parse_time_hint(payload.time_hint)
            if parsed:
                time_start, time_end = parsed

        item = MetadataItem(
            id=item_id or str(uuid.uuid4()),
            actors=payload.actors,
            time_start=time_start,
            time_end=time_end,
            time_hint=payload.time_hint,
            content_type=payload.content_type,
            emotion=payload.emotion,
            intent=payload.intent,
            file_refs=payload.file_refs,
            labels=payload.labels,
            vector=payload.vector,
        )
        metadata_store.upsert(item)
        return item

    def get(self, item_id: str) -> MetadataItem | None:
        return metadata_store.get(item_id)

    def list_all(self):
        return metadata_store.all()


metadata_service = MetadataService()
