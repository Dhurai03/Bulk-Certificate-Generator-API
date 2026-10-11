from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str = "Bulk Certificate Generator API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./certificates.db"

    # Filesystem storage for generated certificates
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    GENERATED_DIR: Path = BASE_DIR / "generated"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Ensure the generated certificates directory exists
settings.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
