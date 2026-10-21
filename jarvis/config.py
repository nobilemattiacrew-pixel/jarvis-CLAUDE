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
    MODEL: str = _get_env("JARVIS_MODEL", "auto")

    # --- FreeLLMAPI (local Anthropic-compatible proxy) ---
    # When JARVIS_AI_PROVIDER=frellapi, JARVIS routes requests through a
    # local FreeLLMAPI server instead of the public Anthropic API.
    FLLMAPI_BASE_URL: str = _get_env("JARVIS_FLLMAPI_BASE_URL", "http://localhost:3001")
    FLLMAPI_API_KEY: str | None = _get_env("JARVIS_FLLMAPI_API_KEY")

    # --- Speech ---
    TTS_RATE: int = _get_int("JARVIS_TTS_RATE", 150)
    TTS_VOLUME: float = _get_float("JARVIS_TTS_VOLUME", 0.9)
    LANGUAGE: str = _get_env("JARVIS_LANGUAGE", "it-IT")
    # Whether to use Google Speech Recognition (online) or fall back to offline
    # Recognizer. Google is the default; set to False to require offline only.
    USE_GOOGLE_RECOGNITION: bool = _get_bool("JARVIS_USE_GOOGLE_RECOGNITION", True)
    # Optional microphone device index (integer). If not set, the default microphone is used.
    MICROPHONE_INDEX: int | None = _get_int("JARVIS_MICROPHONE_INDEX", None)

    # --- Application behavior ---
    ALWAYS_ON_TOP: bool = _get_bool("JARVIS_ALWAYS_ON_TOP", True)
    SYSTEM_TRAY: bool = _get_bool("JARVIS_SYSTEM_TRAY", True)
    LOG_LEVEL: str = _get_env("JARVIS_LOG_LEVEL", "INFO").upper()

    # --- Paths ---
    PROJECT_ROOT: Path = PROJECT_ROOT
    ASSETS_DIR: Path = PROJECT_ROOT / "assets"

    # Synonyms (Italian) for app names – map spoken words to the key used in AUTHORIZED_APPS
    APP_SYNONYMS: dict[str, str] = {
        "calcolatrice": "calc",
        "blocco note": "notepad",
        "blocco": "notepad",
        "chrome": "chrome",
        "firefox": "firefox",
        "edge": "edge",
        "esplora": "explorer",
        "esplora file": "explorer",
    }
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

    # Provider specific key checks
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
    if Config.AI_PROVIDER == "frellapi":
        # FreeLLMAPI expects an endpoint and optionally an API key
        if not Config.FLLMAPI_BASE_URL:
            issues.append(
                "JARVIS_FLLMAPI_BASE_URL non impostata. Specificare l'URL del server FreeLLMAPI."
            )
        # Attempt a quick connectivity check (non‑blocking, short timeout)
        try:
            import requests
            resp = requests.get(Config.FLLMAPI_BASE_URL, timeout=2)
            if resp.status_code >= 400:
                issues.append(
                    f"FreeLLMAPI endpoint returned status {resp.status_code}. Verificare che il server sia attivo."
                )
        except Exception:
            issues.append(
                "Impossibile contattare FreeLLMAPI all'URL configurato. Verificare che il server sia in esecuzione su "
                f"{Config.FLLMAPI_BASE_URL}."
            )
    # General provider validation
    if Config.AI_PROVIDER not in {"anthropic", "openai", "frellapi"}:
        issues.append(
            f"JARVIS_AI_PROVIDER='{Config.AI_PROVIDER}' non valido. "
            "Usare 'anthropic', 'openai' o 'frellapi'."
        )
    if not (0.0 <= Config.TTS_VOLUME <= 1.0):
        issues.append("JARVIS_TTS_VOLUME deve essere tra 0.0 e 1.0.")
    if not (0 <= Config.TTS_RATE <= 200):
        issues.append("JARVIS_TTS_RATE deve essere tra 0 e 200.")

    return issues