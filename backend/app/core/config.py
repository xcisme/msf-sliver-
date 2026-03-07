"""Application configuration using Pydantic Settings."""
import secrets
from typing import Optional

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration."""

    # JWT Configuration
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Metasploit Framework Configuration
    MSF_HOST: str = "192.168.x.x"
    MSF_PORT: int = 55553
    MSF_PASSWORD: str = ""
    MSF_USERNAME: str = "msf"

    # Application Configuration
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Config()
