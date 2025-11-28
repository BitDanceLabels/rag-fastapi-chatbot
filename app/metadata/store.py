from __future__ import annotations

from typing import Dict
from app.metadata.schema import MetadataItem


class MetadataStore:
    """In-memory store for demo. Replace with DB integration when ready."""

    def __init__(self):
        self.items: Dict[str, MetadataItem] = {}

    def upsert(self, item: MetadataItem) -> MetadataItem:
        self.items[item.id] = item
        return item

    def get(self, item_id: str) -> MetadataItem | None:
        return self.items.get(item_id)

    def all(self):
        return list(self.items.values())


metadata_store = MetadataStore()
