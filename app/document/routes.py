from fastapi import APIRouter, UploadFile
from app.document.schema import UploadResponse, ChunkResponse
from app.document.services import DocumentService
from fastapi_pagination import Page, paginate


document_services = DocumentService()
document_router = APIRouter()

@document_router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile):
    file = await document_services.upload_document(file=file)
    return file

@document_router.get("/")
async def preview_document(object_path: str) -> Page[ChunkResponse]:
    file = await document_services.preview_document(object_path=object_path)
    return paginate(file)


