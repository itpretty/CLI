"""Settings management.

The CLI uses the `claude` CLI as its LLM backend by default,
which uses the current logged-in session (Team/Pro subscription).
No API keys needed.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

def _get_package_dir() -> Path:
    """Resolve the package directory, handling PyInstaller frozen bundles."""
    import sys
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle — data files are in sys._MEIPASS
        return Path(sys._MEIPASS) / "proposal"
    return Path(__file__).resolve().parent


_PACKAGE_DIR = _get_package_dir()
TEMPLATES_DIR = _PACKAGE_DIR / "templates"
FONTS_DIR = _PACKAGE_DIR / "fonts"


class Domain(str, Enum):
    STEM = "STEM"
    HUMANITIES = "Humanities"
    SOCIAL_SCIENCES = "Social Sciences"


class Language(str, Enum):
    ENGLISH = "English"
    CHINESE = "Chinese"


class Settings(BaseSettings):
    # Optional API keys — only needed if using direct API providers
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    serper_api_key: str = Field(default="", alias="SERPER_API_KEY")
    serpapi_key: str = Field(default="", alias="SERPAPI_KEY")

    # LLM settings
    agent: str = "claude"  # selected agent binary name
    agent_path: str = ""  # resolved path to agent binary
    model: str = "sonnet"  # model alias
    default_word_count: int = 3000
    default_language: Language = Language.ENGLISH
    default_domain: Domain = Domain.STEM
    max_tokens_per_call: int = 8192

    model_config = {"env_prefix": "", "extra": "ignore"}

    @property
    def has_web_search(self) -> bool:
        return bool(self.serper_api_key or self.serpapi_key)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
