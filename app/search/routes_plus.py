from fastapi import APIRouter, Depends
from app.auth.dependency import AccessTokenBearer
from app.search.schema_plus import SearchPlusRequest, SearchPlusResponse
from app.search.services_plus import SearchPlusService

search_plus_router = APIRouter()
search_plus_service = SearchPlusService()


@search_plus_router.post("/search-plus", response_model=SearchPlusResponse, dependencies=[Depends(AccessTokenBearer())])
async def search_plus(payload: SearchPlusRequest):
    """
    Advanced search with fuzzy time parsing, metadata filters and multi-vector placeholders.
    Currently returns mocked results; replace SearchPlusService.search with real vector search + metadata filtering.
    """
    return search_plus_service.search(payload)
