from fastapi import FastAPI
from app.document_storage.routes import drive_router


app = FastAPI()

app.include_router(drive_router, prefix="/drive", tags=["drive"])