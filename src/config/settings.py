# Configuration Settings

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = Path("./data")
    RAW_DIR: Path = Path("./data/raw")
    INTERMEDIATE_DIR: Path = Path("./data/intermediate")
    CANONICAL_DIR: Path = Path("./data/canonical")
    EVALUATION_DIR: Path = Path("./data/evaluation")
    MANIFESTS_DIR: Path = Path("./data/manifests")

    # Vector Database
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "scientific_docs_chunks"
    QDRANT_USE_SQ8: bool = True
    HNSW_M: int = 16
    HNSW_EF_CONSTRUCT: int = 100

    # Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "scientific_docintel_secret"
    NEO4J_DATABASE: str = "neo4j"

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-3.6-flash"
    GEMINI_API_KEY: str = ""
    MAX_OUTPUT_TOKENS: int = 2048
    TEMPERATURE: float = 0.2
    TOP_P: float = 0.95

    # Local LLM Fallback
    LOCAL_LLM_ENABLED: bool = False
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_LLM_MODEL: str = "Qwen/Qwen2.5-0.5B-Instruct"

    # Embeddings
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384
    EMBEDDING_DEVICE: str = "cpu"

    # Reranking
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_DEVICE: str = "cpu"
    RERANK_TOP_K: int = 50
    FINAL_EVIDENCE_COUNT: int = 8

    # Rendering & Parsing
    RENDER_DPI: int = 150
    PARSER_VERSION: str = "0.1.0"
    SCHEMA_VERSION: str = "1.0.0"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]


settings = AppSettings()
