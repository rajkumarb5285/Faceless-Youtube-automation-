from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True
    AUTONOMY_LEVEL: int = 1  # 0: manual, 1: human script + video gate, 2: QA fail gate, 3: autonomous

    # LLMs
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEFAULT_STRONG_MODEL: str = "openai/gpt-oss-20b"
    DEFAULT_FAST_MODEL: str = "openai/gpt-oss-20b"

    # Databases
    MONGODB_URI: str = "mongodb://localhost:27017/faceless_studio"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Storage
    STORAGE_BACKEND: str = "s3"
    STORAGE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    S3_BUCKET: str = "faceless-studio-media-raj"
    AWS_REGION: str = "ap-south-1"
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None

    # Web search
    SEARCH_PROVIDER: str = "tavily"
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None

    # TTS
    SARVAM_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None

    # YouTube API
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_CLIENT_SECRETS_FILE: str = "client_secret.json"
    YOUTUBE_TOKEN_STORAGE_PATH: str = "./data/tokens"

    # Stock Media APIs (Coverr & Pixabay)
    COVERR_API_KEY: Optional[str] = None
    PIXABAY_API_KEY: Optional[str] = None

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    class Config:
        env_file = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
            ".env"
        ]
        extra = "ignore"

settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
