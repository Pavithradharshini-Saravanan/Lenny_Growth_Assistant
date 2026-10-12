import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "The Lenny Growth Assistant"
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./lenny_growth_assistant.db")

    # Model Provider Settings
    PROVIDER_TYPE: str = os.getenv("PROVIDER_TYPE", "ollama")  # "ollama" or "cloud"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:4b")

    # Cloud Provider Settings (Anthropic Claude)
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY", None)
    CLOUD_MODEL: str = os.getenv("CLOUD_MODEL", "claude-3-5-sonnet-20241022")

    # Second Cloud Provider Settings (Google Gemini)
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    GEMINI_BASE_URL: str = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")

settings = Settings()
