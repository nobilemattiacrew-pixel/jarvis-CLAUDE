#!/usr/bin/env python3
"""Test script to verify JARVIS structure and imports."""

import sys
import os

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        # Test config
        from jarvis.config import Config
        print("✓ Config imported")

        # Test validation (validate is a module-level function)
        from jarvis.config import validate
        issues = validate()
        if issues:
            print(f"⚠ Config validation issues: {issues}")
        else:
            print("✓ Config validation passed")

        # Test LLM client (will fail without API keys, but should import)
        from jarvis.core.llm_client import LLMClient
        print("✓ LLMClient imported")

        # Test engine
        from jarvis.core.engine import Engine
        print("✓ Engine imported")

        # Test modules
        from jarvis.modules.speech import SpeechManager
        print("✓ SpeechManager imported")

        from jarvis.modules.windows_tools import WindowsTools
        print("✓ WindowsTools imported")

        # Test GUI (will fail without display in test env, but should import)
        from jarvis.gui.app import JarvisGUI
        print("✓ JarvisGUI imported")

        # Test utils
        from jarvis.utils.logger import setup_logger, get_logger
        print("✓ Logger utilities imported")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        from jarvis.config import Config

        print(f"AI Provider: {Config.AI_PROVIDER}")
        print(f"Model: {Config.MODEL}")
        print(f"TTS Rate: {Config.TTS_RATE}")
        print(f"TTS Volume: {Config.TTS_VOLUME}")
        print(f"Language: {Config.LANGUAGE}")
        print(f"Always on Top: {Config.ALWAYS_ON_TOP}")
        print(f"System Tray: {Config.SYSTEM_TRAY}")
        print(f"Log Level: {Config.LOG_LEVEL}")

        print(f"Authorized apps: {list(Config.AUTHORIZED_APPS.keys())}")
        print(f"Authorized URLs: {len(Config.AUTHORIZED_URLS)} sites")

        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("JARVIS Structure Test")
    print("=" * 50)

    success = test_imports()
    if success:
        success = test_config_loading()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Structure is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure .env file with your API keys")
        print("3. Run: python main.py")
    else:
        print("💥 Some tests failed. Check the output above.")
    print("=" * 50)