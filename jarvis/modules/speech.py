"""Speech module for JARVIS.

Handles speech recognition (speech-to-text) and text-to-speech (TTS) using
SpeechRecognition and pyttsx3.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Optional

import pyttsx3
import speech_recognition as sr
from jarvis.config import Config
from jarvis.utils.logger import get_logger

logger = get_logger(__name__)


class SpeechManager:
    """Manages speech input and output for JARVIS."""

    def __init__(self) -> None:
        """Initialize the speech manager."""
        self.logger = logger
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self._is_listening = False
        self._listen_thread: Optional[threading.Thread] = None
        self._stop_listening = threading.Event()
        self._microphone_available = False

        # Configure TTS engine from config
        self.tts_engine.setProperty("rate", Config.TTS_RATE)  # words per minute
        self.tts_engine.setProperty("volume", Config.TTS_VOLUME)  # 0.0 to 1.0
        # Try to set an Italian voice if available
        voices = self.tts_engine.getProperty("voices")
        for voice in voices:
            if "italian" in voice.name.lower() or "it" in voice.id.lower():
                self.tts_engine.setProperty("voice", voice.id)
                break

        # Try to initialize microphone (may fail if PyAudio is not installed or no microphone available)
        try:
            self.microphone = sr.Microphone()
            self._microphone_available = True
            self.logger.info("Microphone initialized successfully")
        except Exception as e:
            self.logger.warning(
                f"Microphone not available: {e}. Voice input disabled."
            )
            self._microphone_available = False

        self.logger.info("Speech manager initialized")

    def speak(self, text: str) -> None:
        """Convert text to speech and play it.

        Args:
            text: The text to speak.
        """
        self.logger.debug(f"Speaking: {text}")
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"TTS error: {e}")

    def listen_once(self, timeout: float = 5.0, phrase_time_limit: float = 10.0) -> Optional[str]:
        """Listen for a single phrase from the microphone and return the recognized text.

        Args:
            timeout: Seconds to wait for a phrase to start.
            phrase_time_limit: Maximum seconds for the phrase to continue.

        Returns:
            The recognized text, or None if no speech was detected or an error occurred.
        """
        if not self._microphone_available:
            self.logger.warning("Microphone not available, cannot listen.")
            return None

        with self.microphone as source:
            self.logger.debug("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.logger.debug("Listening for speech...")
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
                self.logger.debug("Recognizing speech...")
                text = self.recognizer.recognize_google(
                    audio, language=Config.LANGUAGE
                )
                self.logger.info(f"Recognized: {text}")
                return text
            except sr.WaitTimeoutError:
                self.logger.debug("Listening timed out while waiting for phrase.")
                return None
            except sr.UnknownValueError:
                self.logger.debug("Speech was unintelligible.")
                return None
            except sr.RequestError as e:
                self.logger.error(f"Could not request results from speech service: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error in speech recognition: {e}")
                return None

    def start_listening(self, callback) -> None:
        """Start background listening for commands.

        Args:
            callback: A function to call with the recognized text.
        """
        if not self._microphone_available:
            self.logger.warning("Microphone not available, cannot start listening.")
            return

        if self._is_listening:
            self.logger.warning("Already listening")
            return

        self._is_listening = True
        self._stop_listening.clear()
        self._listen_thread = threading.Thread(
            target=self._listen_loop, args=(callback,), daemon=True
        )
        self._listen_thread.start()
        self.logger.info("Started background listening")

    def stop_listening(self) -> None:
        """Stop background listening."""
        if not self._is_listening:
            return
        self._is_listening = False
        self._stop_listening.set()
        if self._listen_thread:
            self._listen_thread.join(timeout=2.0)
        self.logger.info("Stopped background listening")

    def _listen_loop(self, callback) -> None:
        """Background loop to continuously listen for speech."""
        if not self._microphone_available:
            self.logger.warning("Microphone not available, cannot start listening loop.")
            return

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while not self._stop_listening.is_set():
                try:
                    audio = self.recognizer.listen(
                        source, timeout=1.0, phrase_time_limit=5.0
                    )
                    text = self.recognizer.recognize_google(
                        audio, language=Config.LANGUAGE
                    )
                    self.logger.debug(f"Background recognized: {text}")
                    callback(text)
                except sr.WaitTimeoutError:
                    # Timeout is expected, just continue
                    continue
                except sr.UnknownValueError:
                    # Speech was unintelligible, just continue
                    continue
                except sr.RequestError as e:
                    self.logger.error(f"Speech service request error: {e}")
                    time.sleep(1)  # Avoid tight loop on error
                except Exception as e:
                    self.logger.error(f"Unexpected error in background listening: {e}")
                    time.sleep(1)