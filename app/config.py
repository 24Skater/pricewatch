from typing import Optional, List
from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application
    app_name: str = "Pricewatch"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///pricewatch.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Scraping
    request_timeout: int = 30
    max_retries: int = 3
    use_js_fallback: bool = False
    schedule_minutes: int = 30
    
    # SMTP (Default/Environment)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    from_email: str = "alerts@example.com"
    
    # Twilio (Default/Environment)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Monitoring
    enable_metrics: bool = False
    metrics_port: int = 9090
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be development, staging, or production")
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
