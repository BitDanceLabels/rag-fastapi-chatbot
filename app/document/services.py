import logging
import tempfile
import hashlib

from fastapi import UploadFile
from app.document.schema import UploadResponse, ChunkResponse
from app.core.minio import get_minio_client, init_minio
from app.config import Config
from pathlib import Path
from io import BytesIO
from app.doc_processing.services import DocProcessing

document_processing_service = DocProcessing(model="google/embeddinggemma-300M", chunk_size=512, chunk_overlap=50)


class DocumentService:
    async def upload_document(self, file: UploadFile) -> UploadResponse:
        """Step 1: Upload document to MinIO"""
        content = await file.read()
        file_size = len(content)

        file_hash = hashlib.sha256(content).hexdigest()

        # Clean and normalize filename
        file_name = "".join(
            c for c in file.filename if c.isalnum() or c in ("-", "_", ".")
        ).strip()
        object_path = f"tmp/{file_name}"

        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".md": "text/markdown",
            ".txt": "text/plain",
        }

        file_path = Path(file_name)
        ext = file_path.suffix
        content_type = content_types.get(ext.lower(), "application/octet-stream")

        # Upload to MinIO
        _minio_client = init_minio()
        minio_client = get_minio_client()
        try:
            minio_client.put_object(
                bucket_name=Config.BUCKET_NAME,
                object_name=object_path,
                data=BytesIO(content),
                length=file_size,
                content_type=content_type,
            )
        except Exception as e:
            logging.error(f"Failed to upload file in MinIO: {str(e)}")
            raise

        return UploadResponse(
            file_path=object_path,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            file_hash=file_hash,
        )

    async def preview_document(self, object_path: str):
        """Step 2: Generate preview chunks"""
        minio_client = get_minio_client()
        file_path = Path(object_path)
        ext = file_path.suffix.lower()

        #Download to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            minio_client.fget_object(
                bucket_name=Config.BUCKET_NAME,
                object_name=object_path,
                file_path=temp_file.name,
            )
            temp_path = temp_file.name
        try:
            # Load and split the document
            all_chunks = document_processing_service.load_and_split(file_path=temp_path)
            return list(ChunkResponse(content=chunk) for chunk in all_chunks)
        finally:
            Path(temp_path).unlink()

