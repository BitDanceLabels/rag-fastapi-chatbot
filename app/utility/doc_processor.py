import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_docling import DoclingLoader
from langchain_community.embeddings import OllamaEmbeddings
from app.config import Config
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = Config.EMBEDDING_MODEL
OLLAMA_HOST = Config.OLLAMA_HOST
PSYCOPG_CONNECT = Config.PSYCOPG_CONNECT

class DocProcessor(DoclingLoader):
    """Class to split tokens from file and chunk it efficiently."""

    # Class-level cache (shared across instances). Singleton instance
    _embedders: dict[str, Any] = {}

    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        model_kwargs: Optional[Dict[str, Any]] = None,
        encode_kwargs: Optional[Dict[str, Any]] = None,
    ):
        # Initialize text splitter (no HF tokenizer needed for Ollama embeddings)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # Load embedder once per model using Ollama
        if model not in DocProcessor._embedders:
            logger.info(f"Loading Ollama embedder for {model}...")
            DocProcessor._embedders[model] = OllamaEmbeddings(
                model=model,
                base_url=OLLAMA_HOST,
            )

        # Assign references
        self.embedder = DocProcessor._embedders[model]

    def load_and_split(self, file_path: str):
        try:
            super().__init__(file_path=file_path)

            for doc in self.lazy_load():  # Load each document chunk
                for chunk in self.text_splitter.split_text(
                    doc.page_content
                ):  # Chunk for each document chunk
                    yield chunk  # This is list [str] type response
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

    def _clean_text(self, text: str) -> str:
        """Clean input text to reduce processing load."""
        import re

        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        # text = re.sub(r"[^\w\s]", "", text)  # Remove special characters (if needed)
        return text.strip()
