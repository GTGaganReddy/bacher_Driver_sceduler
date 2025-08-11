import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase Database - Build connection string with provided credentials
    SUPABASE_PASSWORD: str = os.getenv("SUPABASE_PASSWORD", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL") or f"postgresql://postgres:{os.getenv('SUPABASE_PASSWORD', '')}@db.nqwyglxhvhlrviknykmt.supabase.co:5432/postgres"
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://nqwyglxhvhlrviknykmt.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xd3lnbHhodmhscnZpa255a210Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzQyMTk3OCwiZXhwIjoyMDY4OTk3OTc4fQ.xGolIcNOusVfqpfptE-uSo_eBaSYOx5QI-e9APiTOuA")
    
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
