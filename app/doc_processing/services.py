from sqlmodel import Session

from app.document_storage.services import GoogleDriveService
from fastapi import HTTPException
from googleapiclient.http import MediaIoBaseDownload
import io
import logging
from pathlib import Path
from transformers import AutoTokenizer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_docling import DoclingLoader
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import Config
from googleapiclient.errors import HttpError
from typing import Optional, Dict, Any


google_drive_service = GoogleDriveService()
logger = logging.getLogger(__name__)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = Config.EMBEDDING_MODEL
DATABASE_URL = Config.DATABASE_URL


class DocProcessing(DoclingLoader):
    """Class to download a PDF from Google Drive, chunk it, and delete the file."""

    def __init__(
        self,
        model: str | None = EMBEDDING_MODEL,
        chunk_size: int | None = 256,
        chunk_overlap: int | None = 50,
        model_kwargs: Optional[Dict[str, Any]] = None,
        encode_kwargs: Optional[Dict[str, Any]] = None,
        file_path: str | None = None,
    ):

        if model_kwargs is None:
            model_kwargs = {"device": "cpu"}
        if encode_kwargs is None:
            encode_kwargs = {"normalize_embeddings": True}

        # Initialize without file_path; set later in load_and_split
        super().__init__(file_path=self.file_path)
        self.file_path = file_path

        # Initialize tokenizer and embedder
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.embedder = HuggingFaceEmbeddings(
            model_name=model, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
        )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=self.tokenizer,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def download_and_save(self, file_id: str, output_dir: str = "temp_files"):
        """Download a PDF, preprocess, chunk, print chunks, and delete files."""
        try:
            credentials = google_drive_service.load_credentials()
            if not credentials or not credentials.valid:
                logger.warning("Invalid credentials, re-authentication required")
                raise HTTPException(
                    status_code=401,
                    detail="Could not validate credentials. Please authenticate via /drive/auth",
                )
            drive_service = google_drive_service.get_drive_service(credentials)

            # Get file metadata
            file_metadata = (
                drive_service.files()
                .get(fileId=file_id, fields="name, mimeType")
                .execute()
            )
            file_name = file_metadata.get("name", "downloaded_file")
            mime_type = file_metadata.get("mimeType", "")

            # Verify file is a PDF
            if mime_type != "application/pdf":
                raise HTTPException(
                    status_code=400, detail=f"File is not a PDF: {mime_type}"
                )

            # Download file
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            # Save PDF to disk
            Path(output_dir).mkdir(exist_ok=True)
            temp_file_path = Path(output_dir) / file_name

            self.file_path = str(temp_file_path)

            with open(temp_file_path, "wb") as f:
                f.write(fh.getvalue())

            if not temp_file_path.exists():
                raise HTTPException(
                    status_code=404, detail="File not found after download"
                )

            return {
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
            }

        except HttpError as e:
            status_code = e.resp.status
            if status_code == 404:
                logger.error(f"File not found: {file_id}")
                return {"error": f"File not found: {file_id}"}
            elif status_code == 403:
                logger.error(f"Access denied: {str(e)}")
                return {"error": f"Access denied: {str(e)}"}
            logger.error(f"Google API error: {str(e)}")
            return {"error": f"Google API error: {str(e)}"}
        except HTTPException as e:
            logger.error(f"HTTP error: {e.status_code} - {e.detail}")
            return {"error": f"HTTP error: {e.status_code} - {e.detail}"}
        except Exception as e:
            logger.error(f"Error: {str(e)}")

    def load_and_split(self, file_path: str | None = None):
        """Generator function to yield chunks from the document."""
        if file_path is not None:
            self.file_path = file_path

        if not self.file_path or not Path(self.file_path).exists():
            raise HTTPException(status_code=404, detail="File not found for processing")

        try:
            # Initialize DoclingLoader with text file
            super().__init__(file_path=self.file_path)
            doc_iter = self.lazy_load()
            for doc in doc_iter:
                chunks = self.text_splitter.split_text(doc.page_content)
                yield chunks
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def encode(self, texts):
        """Encode texts using HuggingFaceEmbeddings."""
        try:
            if isinstance(texts, list):
                return self.embedder.embed_documents(texts)
            else:
                return self.embedder.embed_query(texts)
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error encoding texts: {str(e)}")
