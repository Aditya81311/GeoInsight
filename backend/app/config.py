"""
App configuration.

Uses pydantic-settings (not `from pydantic import BaseSettings`, which was
removed in Pydantic v2 and moved into its own package). This is the fix for
the PydanticImportError you hit earlier.
"""

from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GeoInsight API"
    api_v1_prefix: str = "/api/v1"

    # Vite dev server default is 5173. Add more origins if your frontend
    # runs somewhere else (e.g. 3000).
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Where real datasets go (see data/README.md). Relative to backend/ by
    # default, or set an absolute path in .env.
    data_dir: str = "data"

    # Optional: used only for the AI-generated insight (OpenRouter). If not
    # set, a rule-based template insight is used instead — nothing breaks.
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "openai/gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
