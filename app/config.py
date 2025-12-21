from typing import Optional, List, Union, Any, Dict
from pydantic import HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource
from cryptography.fernet import Fernet
import os
import logging
import json


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application
    app_name: str = "Pricewatch"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///pricewatch.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_query_timeout: int = 30  # Query timeout in seconds
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    encryption_key: Optional[str] = None  # Fernet key for encrypting sensitive data
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Scraping
    request_timeout: int = 30
    max_retries: int = 3
    use_js_fallback: bool = False
    use_async_client: bool = False  # Use async HTTP client for API endpoints
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
        # Minimum 32 characters for development, validated further in model_validator for production
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v):
        """Validate encryption key format if provided."""
        # Treat empty strings as None
        if v == "":
            return None
        if v is not None:
            try:
                # Validate it's a valid Fernet key
                Fernet(v.encode() if isinstance(v, str) else v)
            except Exception:
                raise ValueError("Invalid encryption key format. Must be a valid Fernet key.")
        return v
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Customize settings sources to handle comma-separated list fields."""
        # Wrap the dotenv settings source to handle comma-separated strings
        class CommaSeparatedListSource(DotEnvSettingsSource):
            def prepare_field_value(self, field_name: str, field, field_value: Any, value_is_complex: bool) -> Any:
                """Override to handle comma-separated strings for list fields."""
                # Check if this is a list field that might be comma-separated
                if field_name in ["allowed_hosts", "cors_origins"] and isinstance(field_value, str):
                    # Try JSON first
                    try:
                        return json.loads(field_value)
                    except (json.JSONDecodeError, ValueError):
                        # Fall back to comma-separated string
                        return [item.strip() for item in field_value.split(",") if item.strip()]
                # For other fields, use default behavior
                return super().prepare_field_value(field_name, field, field_value, value_is_complex)
        
        return (
            init_settings,
            env_settings,
            CommaSeparatedListSource(settings_cls),
            file_secret_settings,
        )
    
    @model_validator(mode="after")
    def check_production_requirements(self):
        """Ensure required secrets are set in production."""
        if self.environment == "production":
            # Check encryption key
            if not self.encryption_key:
                raise ValueError(
                    "ENCRYPTION_KEY must be set in production environment. "
                    "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )
            
            # Check secret key is not default
            if self.secret_key == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be changed from default in production environment.")
            
            # Require longer secret key in production (64 characters)
            if len(self.secret_key) < 64:
                raise ValueError(
                    "SECRET_KEY must be at least 64 characters in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
        
        elif self.environment == "staging":
            # Staging has similar requirements but allows shorter keys
            if not self.encryption_key:
                raise ValueError("ENCRYPTION_KEY must be set in staging environment.")
            if self.secret_key == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be changed from default in staging environment.")
        
        return self
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def _get_settings() -> Settings:
    """Get settings instance with development warnings."""
    s = Settings()
    if s.environment == "development":
        logger = logging.getLogger("app.config")
        logger.warning(
            "⚠️  Running in DEVELOPMENT mode. "
            "Do not use in production without setting ENVIRONMENT=production"
        )
        if not s.encryption_key:
            logger.warning(
                "⚠️  ENCRYPTION_KEY not set. Using auto-generated key for development. "
                "This key will change on restart - set ENCRYPTION_KEY for persistence."
            )
    return s


# Global settings instance
settings = _get_settings()
