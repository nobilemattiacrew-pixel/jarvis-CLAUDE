import unittest
from unittest.mock import MagicMock, patch
from jarvis import config as cfg


class TestSpeechManager(unittest.TestCase):
    def setUp(self):
        # Patch pyttsx3.init to return a mock engine
        self.patcher_tts_init = patch('pyttsx3.init')
        self.mock_tts_init = self.patcher_tts_init.start()
        self.mock_engine = MagicMock()
        self.mock_tts_init.return_value = self.mock_engine

        # Patch Microphone to a dummy context manager
        self.patcher_mic = patch('speech_recognition.Microphone')
        self.mock_mic_class = self.patcher_mic.start()
        self.mock_mic_instance = MagicMock()
        self.mock_mic_class.return_value.__enter__.return_value = self.mock_mic_instance
        self.mock_mic_class.return_value.__exit__.return_value = None

        # Patch Recognizer to a mock with needed methods
        self.patcher_recognizer = patch('speech_recognition.Recognizer')
        self.mock_recognizer_class = self.patcher_recognizer.start()
        self.mock_recognizer = MagicMock()
        self.mock_recognizer_class.return_value = self.mock_recognizer

        # Ensure Config uses deterministic values
        cfg.Config.USE_GOOGLE_RECOGNITION = True
        cfg.Config.TTS_RATE = 150
        cfg.Config.TTS_VOLUME = 0.9

        # Import SpeechManager after patches
        from jarvis.modules.speech import SpeechManager
        self.SpeechManager = SpeechManager

    def tearDown(self):
        self.patcher_tts_init.stop()
        self.patcher_mic.stop()
        self.patcher_recognizer.stop()

    def test_initialization_sets_tts_and_microphone(self):
        print("\n=== TEST: SpeechManager initialization ===")
        try:
            manager = self.SpeechManager()
            print(f"  -> SpeechManager instance created: {manager!r}")
            print(f"  -> TTS engine: {manager.tts_engine}")
            print(f"  -> Recognizer: {manager.recognizer}")
            print(f"  -> _microphone_available flag: {manager._microphone_available}")
            print(f"  -> _is_listening flag: {manager._is_listening}")

            # Verify TTS engine properties were set
            rate_calls = [c for c in self.mock_engine.setProperty.call_args_list if c.args[0] == 'rate']
            vol_calls = [c for c in self.mock_engine.setProperty.call_args_list if c.args[0] == 'volume']
            print(f"  -> setProperty('rate', ...) calls: {rate_calls}")
            print(f"  -> setProperty('volume', ...) calls: {vol_calls}")

            assert manager._microphone_available is True, "Microphone should be available"
            assert rate_calls, "Expected setProperty('rate', ...) to be called"
            assert vol_calls, "Expected setProperty('volume', ...) to be called"
            self.mock_recognizer_class.assert_called_once()
            print("  RESULT: PASS - TTS engine configured, microphone detected, recognizer created")
        except Exception as e:
            print(f"  RESULT: FAIL - {type(e).__name__}: {e}")
            raise

    def test_speak_calls_engine(self):
        print("\n=== TEST: speak() method ===")
        try:
            manager = self.SpeechManager()
            print(f"  -> Calling manager.speak('Hello world')")
            manager.speak('Hello world')
            say_calls = self.mock_engine.say.call_args_list
            run_calls = self.mock_engine.runAndWait.call_args_list
            print(f"  -> engine.say() calls: {say_calls}")
            print(f"  -> engine.runAndWait() calls: {run_calls}")
            self.mock_engine.say.assert_called_once_with('Hello world')
            self.mock_engine.runAndWait.assert_called_once()
            print("  RESULT: PASS - speak() invoked say() and runAndWait() exactly once")
        except Exception as e:
            print(f"  RESULT: FAIL - {type(e).__name__}: {e}")
            raise

    def test_listen_once_returns_recognized_text(self):
        print("\n=== TEST: listen_once() method ===")
        try:
            mock_audio = MagicMock(name='AudioData')
            self.mock_recognizer.listen.return_value = mock_audio
            self.mock_recognizer.recognize_google.return_value = 'test phrase'
            manager = self.SpeechManager()
            print(f"  -> Calling manager.listen_once(timeout=0.1, phrase_time_limit=0.1)")
            result = manager.listen_once(timeout=0.1, phrase_time_limit=0.1)
            print(f"  -> listen_once() returned: {result}")
            print(f"  -> recognizer.adjust_for_ambient_noise calls: {self.mock_recognizer.adjust_for_ambient_noise.call_args_list}")
            print(f"  -> recognizer.listen calls: {self.mock_recognizer.listen.call_args_list}")
            print(f"  -> recognizer.recognize_google calls: {self.mock_recognizer.recognize_google.call_args_list}")
            assert result == 'test phrase', f"Expected 'test phrase', got {result}"
            self.mock_recognizer.adjust_for_ambient_noise.assert_called()
            self.mock_recognizer.listen.assert_called()
            self.mock_recognizer.recognize_google.assert_called_with(mock_audio, language=cfg.Config.LANGUAGE)
            print("  RESULT: PASS - listen_once() returned recognized text and invoked recognizer methods")
        except Exception as e:
            print(f"  RESULT: FAIL - {type(e).__name__}: {e}")
            raise

    def test_listen_once_returns_none_when_microphone_unavailable(self):
        print("\n=== TEST: listen_once() when microphone unavailable ===")
        try:
            # Simulate Microphone initialization failure
            self.patcher_mic.stop()
            with patch('speech_recognition.Microphone', side_effect=Exception('No mic')):
                manager = self.SpeechManager()
                print(f"  -> _microphone_available flag: {manager._microphone_available}")
                print(f"  -> Calling manager.listen_once()")
                result = manager.listen_once()
                print(f"  -> listen_once() returned: {result}")
                assert manager._microphone_available is False, "Microphone should be unavailable"
                assert result is None, "listen_once() should return None when microphone unavailable"
                print("  RESULT: PASS - microphone unavailable, listen_once() returned None")
        except Exception as e:
            print(f"  RESULT: FAIL - {type(e).__name__}: {e}")
            raise


if __name__ == '__main__':
    unittest.main()