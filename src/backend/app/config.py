"""Configuración de la aplicación desde variables de entorno."""

# pylint: disable=too-few-public-methods
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings de la aplicación, cargados desde variables de entorno."""

    # Set via DATABASE_URL env var. Default is for local development only.
    database_url: str = "postgresql://localhost/splitwise"
    app_env: str = "development"
    port: int = 8000
    app_name: str = "Split de Gastos API"
    app_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
