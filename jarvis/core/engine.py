"""Orchestration engine for JARVIS.

Coordinates between LLM, speech, modules, and GUI.
Manages the conversation state and handles user intents.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from jarvis.config import Config
from jarvis.core.llm_client import LLMClient
from jarvis.modules.speech import SpeechManager
from jarvis.modules.windows_tools import WindowsTools
from jarvis.utils.logger import get_logger

logger = get_logger(__name__)


class Engine:
    """Main orchestration engine for JARVIS."""

    def __init__(self) -> None:
        """Initialize the engine and its components."""
        self.logger = logger
        self.llm = LLMClient()
        self.speech = SpeechManager()
        self.windows_tools = WindowsTools()

        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = (
            "Sei JARVIS, un assistente AI personale ispirato a Iron Man. "
            "Rispondi sempre in italiano, con un tono elegante, professionale e leggermente futuristico. "
            "Sei progettato per aiutare l'utente con compiti quotidiani, fornire informazioni e controllare il PC Windows in modo sicuro."
        )

        # Initialize conversation with system prompt
        self.conversation_history.append({"role": "system", "content": self.system_prompt})

        self.logger.info("JARVIS Engine initialized")

    def process_user_input(self, user_text: str) -> str:
        """Process user text input and generate a response.

        Args:
            user_text: The user's input text (from speech or typing).

        Returns:
            The assistant's response text.
        """
        self.logger.debug(f"Processing user input: {user_text}")

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_text})

        # Check for command intents (open app/website, etc.)
        intent_result = self._check_intents(user_text)
        if intent_result:
            # If intent handled, return the result
            return intent_result

        # Otherwise, send to LLM
        try:
            response = self.llm.chat_completion(
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as e:
            self.logger.error(f"Failed to get LLM response: {e}")
            response = "Mi dispiace, si è verificato un errore nel processare la tua richiesta."

        # Add assistant response to history
        self.conversation_history.append({"role": "assistant", "content": response})

        # Trim history if too long (keep last 20 exchanges + system)
        if len(self.conversation_history) > 21:  # system + 20 exchanges
            self.conversation_history = [
                self.conversation_history[0]  # system
            ] + self.conversation_history[-20:]

        return response

    def _check_intents(self, user_text: str) -> Optional[str]:
        """Check if the user text matches any known intents (commands).

        Currently supports:
        - Aprire applicazioni autorizzate
        - Aprire siti web autorizzati
        - Fermare l'ascolto (if in voice mode)

        Returns:
            A response string if intent matched, None otherwise.
        """
        text_lower = user_text.lower().strip()

        # Open authorized applications (including Italian synonyms)
        for app_key, app_exe in Config.AUTHORIZED_APPS.items():
            # Direct match using the canonical key
            if f"apri {app_key}" in text_lower or f"lancia {app_key}" in text_lower:
                self.logger.info(f"Opening authorized app (direct key): {app_key}")
                success = self.windows_tools.open_application(app_exe)
                if success:
                    return f"Sto aprendo {app_key}."
                else:
                    return f"Non riesco ad aprire {app_key}. Verifica che sia installato."
            # Check synonyms mapping if defined
            if hasattr(Config, "APP_SYNONYMS"):
                for synonym, canonical in Config.APP_SYNONYMS.items():
                    if synonym in text_lower:
                        # Use the canonical key to fetch the executable
                        canonical_exe = Config.AUTHORIZED_APPS.get(canonical)
                        if canonical_exe:
                            self.logger.info(f"Opening authorized app via synonym '{synonym}' -> '{canonical}'")
                            success = self.windows_tools.open_application(canonical_exe)
                            if success:
                                return f"Sto aprendo {canonical}."
                            else:
                                return f"Non riesco ad aprire {canonical}. Verifica che sia installato."
                        # If synonym matched but no executable configured, skip (still safe)

        # Open authorized websites
        for site in Config.AUTHORIZED_URLS:
            # Simple check: if the site name (without protocol) is in the text
            site_name = site.replace("https://www.", "").replace("https://", "").rstrip("/")
            site_base = site_name.split(".")[0]
            if (
                f"apri {site_name}" in text_lower
                or f"vai a {site_name}" in text_lower
                or f"apri {site_base}" in text_lower
                or f"vai a {site_base}" in text_lower
            ):
                self.logger.info(f"Opening authorized website: {site}")
                success = self.windows_tools.open_website(site)
                if success:
                    return f"Sto aprendo {site_name}."
                else:
                    return f"Non riesco ad aprire {site_name}."

        # Stop listening intent (if using voice)
        if "ferma" in text_lower and ("ascolto" in text_lower or "microfono" in text_lower):
            self.logger.info("Stop listening intent detected")
            return "OK, ho disattivato l'ascolto vocale."

        # No intent matched
        return None

    def reset_conversation(self) -> None:
        """Reset conversation history to just the system prompt."""
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
        self.logger.info("Conversation history reset")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Return a copy of the conversation history."""
        return self.conversation_history.copy()