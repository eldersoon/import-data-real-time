"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None

    # AWS SQS
    aws_endpoint_url: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    sqs_queue_url: str

    # Application
    upload_dir: str = "./uploads"
    log_level: str = "INFO"
    batch_size: int = 1000
    secret_key: str = "dev-secret-key"

    # API
    api_title: str = "Vehicle Import API"
    api_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""


settings = Settings()
