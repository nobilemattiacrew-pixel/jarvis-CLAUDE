"""Configuration management for JARVIS.

Loads settings from environment variables (via .env file) and provides
a single source of truth for all configuration values. No secrets are
hard-coded in the source code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env file from project root if present
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_env(name: str, default: Any = None) -> Any:
    """Return the value of an environment variable, or the default."""
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


def _get_bool(name: str, default: bool = False) -> bool:
    """Return a boolean from an environment variable."""
    raw = _get_env(name, None)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    """Return an integer from an environment variable."""
    raw = _get_env(name, None)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    """Return a float from an environment variable."""
    raw = _get_env(name, None)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


class Config:
    """Centralized configuration for JARVIS."""

    # --- AI / LLM Provider ---
    AI_PROVIDER: str = _get_env("JARVIS_AI_PROVIDER", "anthropic").lower()
    ANTHROPIC_API_KEY: str | None = _get_env("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: str | None = _get_env("OPENAI_API_KEY")
    MODEL: str = _get_env("JARVIS_MODEL", "claude-3-5-sonnet-20241022")

    # --- Speech ---
    TTS_RATE: int = _get_int("JARVIS_TTS_RATE", 150)
    TTS_VOLUME: float = _get_float("JARVIS_TTS_VOLUME", 0.9)
    LANGUAGE: str = _get_env("JARVIS_LANGUAGE", "it-IT")

    # --- Application behavior ---
    ALWAYS_ON_TOP: bool = _get_bool("JARVIS_ALWAYS_ON_TOP", True)
    SYSTEM_TRAY: bool = _get_bool("JARVIS_SYSTEM_TRAY", True)
    LOG_LEVEL: str = _get_env("JARVIS_LOG_LEVEL", "INFO").upper()

    # --- Paths ---
    PROJECT_ROOT: Path = PROJECT_ROOT
    ASSETS_DIR: Path = PROJECT_ROOT / "assets"

    # --- Security: whitelist of authorized actions ---
    # These are the ONLY applications and websites JARVIS is allowed to open
    # without explicit user confirmation. Edit in .env or via the config.
    AUTHORIZED_APPS: dict[str, str] = {
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "explorer": "explorer.exe",
        "notepad": "notepad.exe",
        "calc": "calc.exe",
    }

    AUTHORIZED_URLS: list[str] = [
        "https://www.google.com",
        "https://www.youtube.com",
        "https://www.github.com",
        "https://www.stackoverflow.com",
    ]


def validate() -> list[str]:
    """Validate configuration and return a list of warnings/errors.

    Returns:
        List of human-readable validation messages (empty if valid).
    """
    issues: list[str] = []

    if Config.AI_PROVIDER == "anthropic" and not Config.ANTHROPIC_API_KEY:
        issues.append(
            "ANTHROPIC_API_KEY non impostata. Impostare la chiave API in .env "
            "o cambiare JARVIS_AI_PROVIDER."
        )
    if Config.AI_PROVIDER == "openai" and not Config.OPENAI_API_KEY:
        issues.append(
            "OPENAI_API_KEY non impostata. Impostare la chiave API in .env "
            "o cambiare JARVIS_AI_PROVIDER."
        )
    if Config.AI_PROVIDER not in {"anthropic", "openai"}:
        issues.append(
            f"JARVIS_AI_PROVIDER='{Config.AI_PROVIDER}' non valido. "
            "Usare 'anthropic' o 'openai'."
        )
    if not (0.0 <= Config.TTS_VOLUME <= 1.0):
        issues.append("JARVIS_TTS_VOLUME deve essere tra 0.0 e 1.0.")
    if not (0 <= Config.TTS_RATE <= 200):
        issues.append("JARVIS_TTS_RATE deve essere tra 0 e 200.")

    return issues