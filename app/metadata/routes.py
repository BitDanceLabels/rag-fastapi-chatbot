from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependency import AccessTokenBearer
from app.metadata.schema import MetadataPayload, MetadataItem
from app.metadata.services import metadata_service

metadata_router = APIRouter()


@metadata_router.post("/metadata", response_model=MetadataItem, dependencies=[Depends(AccessTokenBearer())])
async def upsert_metadata(payload: MetadataPayload):
    item = metadata_service.upsert(payload)
    return item


@metadata_router.get("/metadata/{item_id}", response_model=MetadataItem, dependencies=[Depends(AccessTokenBearer())])
async def get_metadata(item_id: str):
    item = metadata_service.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return item
