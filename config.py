from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Bot settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    
    # Sanayi panel settings
    SANAYI_API_BASE_URL: str = "https://api.sanayi.panel"
    SANAYI_API_KEY: str
    SANAYI_API_SECRET: str
    
    # Server settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database settings (optional for future use)
    DATABASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
