import unittest
from unittest.mock import patch, MagicMock

from jarvis.core.engine import Engine
from jarvis.config import Config

class TestEngineIntents(unittest.TestCase):
    def setUp(self):
        # Ensure Config values are as expected
        Config.AUTHORIZED_APPS = {
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "explorer": "explorer.exe",
            "notepad": "notepad.exe",
            "calc": "calc.exe",
        }
        Config.APP_SYNONYMS = {
            "calcolatrice": "calc",
            "blocco note": "notepad",
            "blocco": "notepad",
            "chrome": "chrome",
            "firefox": "firefox",
            "edge": "edge",
            "esplora": "explorer",
            "esplora file": "explorer",
        }
        Config.AUTHORIZED_URLS = ["https://www.google.com"]

    @patch('jarvis.modules.windows_tools.WindowsTools.open_application')
    def test_open_calc(self, mock_open):
        mock_open.return_value = True
        engine = Engine()
        response = engine._check_intents('apri calcolatrice')
        self.assertEqual(response, 'Sto aprendo calc.')
        mock_open.assert_called_once_with('calc.exe')

    @patch('jarvis.modules.windows_tools.WindowsTools.open_application')
    def test_open_notepad(self, mock_open):
        mock_open.return_value = True
        engine = Engine()
        response = engine._check_intents('apri blocco note')
        self.assertEqual(response, 'Sto aprendo notepad.')
        mock_open.assert_called_once_with('notepad.exe')

    @patch('jarvis.modules.windows_tools.WindowsTools.open_application')
    def test_open_explorer(self, mock_open):
        mock_open.return_value = True
        engine = Engine()
        response = engine._check_intents('apri explorer')
        self.assertEqual(response, 'Sto aprendo explorer.')
        mock_open.assert_called_once_with('explorer.exe')

    @patch('jarvis.modules.windows_tools.WindowsTools.open_website')
    def test_open_google(self, mock_open):
        mock_open.return_value = True
        engine = Engine()
        response = engine._check_intents('vai a google')
        self.assertEqual(response, 'Sto aprendo google.com.')
        mock_open.assert_called_once_with('https://www.google.com')

if __name__ == '__main__':
    unittest.main()
