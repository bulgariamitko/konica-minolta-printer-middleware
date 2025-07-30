"""Configuration models."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///./printer_middleware.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    api_prefix: str = Field(default="/api/v1")


class SNMPConfig(BaseModel):
    """SNMP configuration."""
    community: str = Field(default="public")
    version: str = Field(default="2c")
    timeout: int = Field(default=5)
    retries: int = Field(default=3)


class JobConfig(BaseModel):
    """Job processing configuration."""
    max_concurrent_jobs: int = Field(default=5)
    job_timeout_seconds: int = Field(default=300)
    retry_attempts: int = Field(default=3)
    cleanup_completed_jobs_after_hours: int = Field(default=24)
    max_file_size_mb: int = Field(default=100)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    file: Optional[str] = Field(default="./logs/middleware.log")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    max_bytes: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field(default="sqlite:///./printer_middleware.db")
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    debug: bool = Field(default=False)
    
    # Printer IPs (set via environment variables)
    printer_c654e_ip: str = Field(default="")
    printer_c654e_password: str = Field(default="")
    printer_c759_ip: str = Field(default="")
    printer_c754e_ip: str = Field(default="")
    printer_km2100_ip: str = Field(default="")
    
    # SNMP
    snmp_community: str = Field(default="public")
    snmp_version: str = Field(default="2c")
    
    # Jobs
    max_concurrent_jobs: int = Field(default=5)
    job_timeout_seconds: int = Field(default=300)
    retry_attempts: int = Field(default=3)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default="./logs/middleware.log")
    
    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class Config(BaseModel):
    """Main configuration model."""
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    snmp: SNMPConfig = Field(default_factory=SNMPConfig)
    jobs: JobConfig = Field(default_factory=JobConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Runtime settings
    settings: Settings = Field(default_factory=Settings)
    
    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment and defaults."""
        settings = Settings()
        
        return cls(
            database=DatabaseConfig(url=settings.database_url),
            api=APIConfig(
                host=settings.api_host,
                port=settings.api_port,
                debug=settings.debug
            ),
            snmp=SNMPConfig(
                community=settings.snmp_community,
                version=settings.snmp_version
            ),
            jobs=JobConfig(
                max_concurrent_jobs=settings.max_concurrent_jobs,
                job_timeout_seconds=settings.job_timeout_seconds,
                retry_attempts=settings.retry_attempts
            ),
            logging=LoggingConfig(
                level=settings.log_level,
                file=settings.log_file
            ),
            settings=settings
        )