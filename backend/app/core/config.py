"""
Application Configuration
Loads settings from environment variables
"""

from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "postgresql://codevoyage:devpassword@localhost:5432/codevoyage"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600
    REDIS_CACHE_PREFIX: str = "codevoyage:cache:"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TIMEOUT: int = 3600
    CELERY_MAX_RETRIES: int = 3
    CELERY_WORKER_CONCURRENCY: int = 4
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 2000
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_RATE_LIMIT: int = 5000
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 500
    TEMP_STORAGE_PATH: str = "/tmp/codevoyage"
    
    # Analysis
    MAX_COMMITS_TO_ANALYZE: int = 2000
    BATCH_SIZE: int = 100
    ENABLE_AI_INSIGHTS: bool = False
    GIT_CLONE_DEPTH: int = 2000
    COMMIT_STATS_LIMIT: int = 1000
    MAX_FILES_FOR_COMPLEXITY: int = 2000

    @model_validator(mode="after")
    def validate_ai_settings(self):
        if self.ENABLE_AI_INSIGHTS and not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required when ENABLE_AI_INSIGHTS=true. "
                "Set ENABLE_AI_INSIGHTS=false to run without AI."
            )
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
