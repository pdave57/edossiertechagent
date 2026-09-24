from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "edossier-llm-agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/edossier")
    DB_ECHO: bool = False
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # OpenRouter (OpenAI-compatible API)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 4000
    
    VECTOR_TABLE_NAME: str = "document_embeddings"
    VECTOR_DIMENSION: int = 1536
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    GO_BACKEND_URL: str = os.getenv("GO_BACKEND_URL", "http://localhost:34006")
    GO_BACKEND_TIMEOUT: int = 30
    
    ML_RECOMMENDER_URL: str = os.getenv("ML_RECOMMENDER_URL", "http://localhost:9001")
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()