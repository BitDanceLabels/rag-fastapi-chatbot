from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL_ASYNCPG_DRIVER: str
    DATABASE_URL_PSYCOPG_DRIVER: str
    PSYCOPG_CONNECT: str
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    BUCKET_NAME: str

    SECRET_KEY: str
    SALT: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    JTI_EXPIRY_SECOND: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    REDIS_URL: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str

    BROKER_URL: str
    BACKEND_URL: str

    EMBEDDING_MODEL: str
    LLM_MODEL: str
    OLLAMA_HOST: str

    DOMAIN_NAME: str
    VERSION: str

    # Optional knobs for RAG/hybrid search backends
    VESPA_HOST: Optional[str] = None
    VESPA_PORT: Optional[int] = None
    VECTOR_BACKEND: Optional[str] = None  # pg|milvus|vespa|local
    HYBRID_LEX_K: int = 20
    HYBRID_VEC_K: int = 20
    RERANK_TOP_N: int = 15
    RERANK_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: Optional[str] = None

    # Gateway registration (optional)
    GATEWAY_URL: Optional[str] = None
    SERVICE_BASE_URL: Optional[str] = None
    SERVICE_NAME: Optional[str] = None
    GATEWAY_PREFIX: str = ""
    REGISTER_RETRIES: int = 5
    REGISTER_DELAY: float = 1.0

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")


Config = Settings()

# Celery config
broker_url = Config.BROKER_URL
backend_url = Config.BACKEND_URL
broker_connection_retry_on_startup = True
