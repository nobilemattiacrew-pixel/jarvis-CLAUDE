"""Main GUI application for JARVIS.

Provides a futuristic, dark-themed desktop interface with chat capabilities,
voice input/output, and integration with the JARVIS engine.
"""

from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from PyQt6.QtGui import QFont, QTextCursor, QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSystemTrayIcon,
    QMenu,
    QLabel,
    QFrame,
)

from jarvis.config import Config
from jarvis.core.engine import Engine
from jarvis.modules.speech import SpeechManager
from jarvis.utils.logger import get_logger

logger = get_logger(__name__)


class WorkerThread(QThread):
    """Worker thread for handling LLM requests to avoid blocking the GUI."""

    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, engine: Engine, user_text: str):
        super().__init__()
        self.engine = engine
        self.user_text = user_text

    def run(self) -> None:
        """Process the user input in a separate thread."""
        try:
            response = self.engine.process_user_input(self.user_text)
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Error in worker thread: {e}")
            self.error_occurred.emit(str(e))


class JarvisGUI(QMainWindow):
    """Main window for the JARVIS GUI."""

    voice_recognized = pyqtSignal(str)
    voice_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = logger
        self.engine = Engine()
        self.speech = SpeechManager()
        self.worker_thread: Optional[WorkerThread] = None

        self._setup_ui()
        self._setup_tray()
        self._connect_signals()
        self._apply_styles()
        self._show_welcome_message()

        self.logger.info("JARVIS GUI initialized")

    def _connect_signals(self) -> None:
        """Connect internal signals.

        Connects voice_recognized and voice_error to their handlers.
        """
        self.voice_recognized.connect(self._handle_voice_result)
        self.voice_error.connect(self._handle_voice_error)

    @pyqtSlot(str)
    def _handle_voice_result(self, text: str) -> None:
        """Handle successful voice recognition.

        Inserts the recognized text into the input field and triggers sending.
        """
        self.input_field.setText(text)
        self._send_message()

    @pyqtSlot(str)
    def _handle_voice_error(self, error_msg: str) -> None:
        """Handle voice recognition errors without crashing.

        Logs the error and shows a status message.
        """
        logger.error(f"Voice thread error: {error_msg}")
        self.status_label.setText("● Errore voce")
        self.status_label.setStyleSheet("color: #ff4444;")
        # Keep GUI alive – do not re‑raise.

    # ---------------------------------------------------------------------
    # Existing UI/setup methods (unchanged) follow unchanged up to the end of file.

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("JARVIS - AI Assistant")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title bar with JARVIS logo and status
        title_layout = QHBoxLayout()
        title_label = QLabel("JARVIS")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # Status indicators
        self.status_label = QLabel("● Pronto")
        self.status_label.setObjectName("statusLabel")
        title_layout.addWidget(self.status_label)

        layout.addLayout(title_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setReadOnly(True)
        self.chat_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.chat_display, stretch=1)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Scrivi un messaggio o premi il microfono per parlare...")
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field, stretch=1)

        self.send_button = QPushButton("Invia")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_button)

        self.voice_button = QPushButton()
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.setFixedSize(50, 50)
        self.voice_button.setToolTip("Premi e parla")
        self.voice_button.pressed.connect(self._start_voice_input)
        self.voice_button.released.connect(self._stop_voice_input)
        input_layout.addWidget(self.voice_button)

        layout.addLayout(input_layout)

        # Set always-on-top if configured
        if Config.ALWAYS_ON_TOP:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

    def _setup_tray(self) -> None:
        """Set up the system tray icon."""
        if not Config.SYSTEM_TRAY:
            return

        self.tray_icon = QSystemTrayIcon(self)
        # Use a placeholder icon - in production, replace with actual JARVIS icon
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))

        tray_menu = QMenu()
        show_action = QAction("Mostra", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("Esci", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self._tray_icon_activated)

    def _tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def _connect_signals(self) -> None:
        """Connect signals and slots.

        Connects voice recognition and error signals to their handlers.
        """
        # Worker thread signals are already connected in _send_message
        # Connect voice signals
        self.voice_recognized.connect(self._handle_voice_result)
        self.voice_error.connect(self._handle_voice_error)


    def _apply_styles(self) -> None:
        """Apply the dark futuristic stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #00bfff;
                letter-spacing: 2px;
            }
            QLabel#statusLabel {
                font-size: 14px;
                color: #00ff00;
                padding: 5px;
            }
            QTextEdit#chatDisplay {
                background-color: #111111;
                border: 2px solid #003366;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                color: #e0e0e0;
                selection-background-color: #0066cc;
            }
            QLineEdit#inputField {
                background-color: #1a1a1a;
                border: 2px solid #003366;
                border-radius: 25px;
                padding: 12px 20px;
                font-size: 14px;
                color: #e0e0e0;
                selection-background-color: #0066cc;
            }
            QLineEdit#inputField:focus {
                border: 2px solid #00bfff;
                background-color: #222222;
            }
            QPushButton#sendButton {
                background-color: #0066cc;
                border: none;
                border-radius: 25px;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton#sendButton:hover {
                background-color: #0080ff;
            }
            QPushButton#sendButton:pressed {
                background-color: #0052a3;
            }
            QPushButton#voiceButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #003366, stop:1 #001f4d);
                border: 2px solid #00bfff;
                border-radius: 25px;
                color: #00bfff;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton#voiceButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #004080, stop:1 #002a66);
                border: 2px solid #00ffff;
            }
            QPushButton#voiceButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #002653, stop:1 #001a33);
                border: 2px solid #0080ff;
            }
        """)

    def _show_welcome_message(self) -> None:
        """Show the initial welcome message."""
        welcome_msg = (
            "<span style='color: #00bfff;'>■</span> "
            "<span style='color: #e0e0e0;'>JARVIS online. "
            "Sistema inizializzato. Come posso assisterti oggi?</span>"
        )
        self._append_message(welcome_msg, is_user=False)

    def _append_message(self, message: str, is_user: bool = False) -> None:
        """Append a message to the chat display.

        Args:
            message: The message text (can contain HTML).
            is_user: True if this is a user message, False for assistant.
        """
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

        if is_user:
            # User message - aligned right, blue accent
            html = f'''
            <div style="margin: 10px 0; text-align: right;">
                <span style="
                    display: inline-block;
                    background-color: #003366;
                    color: #e0e0e0;
                    padding: 10px 15px;
                    border-radius: 18px 18px 4px 18px;
                    max-width: 70%;
                    font-size: 14px;
                    border: 1px solid #0066cc;
                ">
                    {message}
                </span>
            </div>
            '''
        else:
            # Assistant message - aligned left, cyan accent
            html = f'''
            <div style="margin: 10px 0; text-align: left;">
                <span style="
                    display: inline-block;
                    background-color: #001f4d;
                    color: #e0e0e0;
                    padding: 10px 15px;
                    border-radius: 18px 18px 18px 4px;
                    max-width: 70%;
                    font-size: 14px;
                    border: 1px solid #00bfff;
                ">
                    {message}
                </span>
            </div>
            '''

        self.chat_display.insertHtml(html)
        self.chat_display.insertPlainText("\n")
        self.chat_display.ensureCursorVisible()

    def _send_message(self) -> None:
        """Handle sending a message from the input field."""
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        self._append_message(user_text, is_user=True)
        self.input_field.clear()

        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.voice_button.setEnabled(False)
        self.status_label.setText("● Elaborazione...")
        self.status_label.setStyleSheet("color: #ffcc00;")

        # Start worker thread
        self.worker_thread = WorkerThread(self.engine, user_text)
        self.worker_thread.response_ready.connect(self._on_response_ready)
        self.worker_thread.error_occurred.connect(self._on_error)
        self.worker_thread.start()

    @pyqtSlot(str)
    def _on_response_ready(self, response: str) -> None:
        """Handle response from the worker thread (runs in GUI thread)."""
        self._append_message(response, is_user=False)
        self._reset_input_state()

        # Speak the response if TTS is available
        if hasattr(self, 'speech'):
            self.speech.speak(response)

    def _on_error(self, error: str) -> None:
        """Handle error from the worker thread."""
        error_msg = f"Errore: {error}"
        self._append_message(error_msg, is_user=False)
        self._reset_input_state()
        self.status_label.setText("● Errore")
        self.status_label.setStyleSheet("color: #ff4444;")

    def _reset_input_state(self) -> None:
        """Reset input controls to normal state."""
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.voice_button.setEnabled(True)
        self.status_label.setText("● Pronto")
        self.status_label.setStyleSheet("color: #00ff00;")

    def _start_voice_input(self) -> None:
        """Start voice input when the voice button is pressed."""
        self.voice_button.setText("■")
        self.voice_button.setStyleSheet("""
            QPushButton#voiceButton {
                background-color: #ff4444;
                border: 2px solid #ff6666;
                border-radius: 25px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        self.status_label.setText("● Ascolto...")
        self.status_label.setStyleSheet("color: #ffcc00;")

        # Listen in a separate thread to avoid blocking GUI
        from threading import Thread
        Thread(target=self._process_voice_input, daemon=True).start()

    def _stop_voice_input(self) -> None:
        """Stop voice input when the voice button is released."""
        self.voice_button.setText("🎤")
        self.voice_button.setStyleSheet("""
            QPushButton#voiceButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #003366, stop:1 #001f4d);
                border: 2px solid #00bfff;
                border-radius: 25px;
                color: #00bfff;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton#voiceButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #004080, stop:1 #002a66);
                border: 2px solid #00ffff;
            }
            QPushButton#voiceButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #002653, stop:1 #001a33);
                border: 2px solid #0080ff;
            }
        """)
        # Status will be updated by _process_voice_input

    def _process_voice_input(self) -> None:
        """Process voice input in a background thread.

        Emits ``voice_recognized`` with the recognized text or ``voice_error``
        with an error message. This prevents uncaught exceptions from
        terminating the GUI.
        """
        try:
            text = self.speech.listen_once(timeout=3.0, phrase_time_limit=5.0)
            if text:
                self.voice_recognized.emit(text)
            else:
                # No speech detected – emit a harmless error message
                self.voice_error.emit("No speech detected")
        except Exception as e:
            self.voice_error.emit(str(e))

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if Config.SYSTEM_TRAY and hasattr(self, 'tray_icon'):
            self.hide()
            event.ignore()
            self.tray_icon.showMessage(
                "JARVIS",
                "L'applicazione è ancora in esecuzione in background.\n"
                "Fai clic sull'icona nella barra delle applicazioni per ripristinarla.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        else:
            # Actually quit
            self.speech.stop_listening()
            event.accept()


def main() -> None:
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setApplicationVersion("1.0.0")

    # Set application style
    app.setStyle("Fusion")

    window = JarvisGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()