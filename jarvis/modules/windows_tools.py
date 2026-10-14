"""Windows tools module for JARVIS.

Provides safe, whitelisted functions to open authorized applications and websites.
"""

from __future__ import annotations

import logging
import subprocess
import webbrowser
from typing import Optional

from jarvis.config import Config
from jarvis.utils.logger import get_logger

logger = get_logger(__name__)


class WindowsTools:
    """Provides safe interaction with Windows OS."""

    def open_application(self, app_exe: str) -> bool:
        """Open an authorized application by its executable name.

        Args:
            app_exe: The executable name (e.g., "chrome.exe", "notepad.exe").

        Returns:
            True if the application was opened successfully, False otherwise.
        """
        # Verify the app is in the authorized list (double-check)
        if app_exe not in Config.AUTHORIZED_APPS.values():
            logger.warning(f"Attempt to open unauthorized application: {app_exe}")
            return False

        try:
            # Using subprocess.Popen to open the application
            subprocess.Popen(app_exe)
            logger.info(f"Opened application: {app_exe}")
            return True
        except FileNotFoundError:
            logger.error(f"Application not found: {app_exe}")
            return False
        except Exception as e:
            logger.error(f"Failed to open {app_exe}: {e}")
            return False

    def open_website(self, url: str) -> bool:
        """Open an authorized website in the default browser.

        Args:
            url: The website URL to open.

        Returns:
            True if the website was opened successfully, False otherwise.
        """
        # Verify the URL is in the authorized list (double-check)
        if url not in Config.AUTHORIZED_URLS:
            logger.warning(f"Attempt to open unauthorized website: {url}")
            return False

        try:
            webbrowser.open(url)
            logger.info(f"Opened website: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open website {url}: {e}")
            return False