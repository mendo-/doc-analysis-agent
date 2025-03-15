"""Configuration settings for the document analysis system."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChromaDBSettings(BaseSettings):
    """ChromaDB connection settings."""

    host: str = Field(default="localhost", description="ChromaDB server host")
    port: int = Field(default=8000, description="ChromaDB server port")
    collection_name: str = Field(
        default="documents", description="Default collection name"
    )
    persist_directory: Optional[str] = Field(
        default=None, description="Data persistence directory"
    )

    model_config = SettingsConfigDict(
        env_prefix="CHROMA_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class Settings(BaseSettings):
    """Global application settings."""

    # Environment configuration
    environment: str = Field(
        default="development",
        description="Runtime environment (development/test/production)",
    )
    debug: bool = Field(default=False, description="Debug mode flag")

    # Service configuration
    chroma: ChromaDBSettings = Field(default_factory=ChromaDBSettings)
    anthropic_api_key: str = Field(
        default="", description="Anthropic API key for Claude"
    )

    # Test configuration
    is_test: bool = Field(default=False, description="Whether running in test mode")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @classmethod
    def load(cls, load_test_env: bool = False) -> "Settings":
        """Load settings with optional test environment.

        Args:
            load_test_env: Whether to load and prefer .env.test over .env

        Returns:
            Settings: Configuration instance
        """
        # Determine which env files to load and in what order
        env_files = [".env"]
        if load_test_env:
            env_files.append(".env.test")

        # Create settings with the appropriate env files
        settings = cls(_env_file=env_files, is_test=load_test_env)

        # If test env is loaded, ensure test-specific settings are applied
        if load_test_env:
            settings.environment = "test"
            # Use test collection to avoid conflicts
            settings.chroma.collection_name = f"test_{settings.chroma.collection_name}"

        return settings

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_api_key(cls, v: str, info) -> str:
        """Validate that API key is provided when not in test mode."""
        if not v and info.data.get("environment") != "test":
            raise ValueError("ANTHROPIC_API_KEY must be set in non-test environments")
        return v


# Global settings instance - use base config by default
settings = Settings.load()
