#!/usr/bin/env python3
"""Main entry point for JARVIS AI Assistant."""

import sys
import os

# Add the current directory to the path so we can import jarvis
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvis.gui.app import main

if __name__ == "__main__":
    main()