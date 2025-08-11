import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@db.project.supabase.co:5432/postgres")
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    
    # Google Cloud Function
    GCF_URL: str = os.getenv("GCF_URL", "https://your-gcf-url.com/update-sheet")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", "8000"))
    WEEK_DAYS: int = int(os.getenv("WEEK_DAYS", "7"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"

settings = Settings()
