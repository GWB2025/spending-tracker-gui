#!/usr/bin/env python3
"""
Spending Tracker GUI - Main Entry Point

A desktop GUI application for tracking personal spending using Google Sheets.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gui.main_window import main as run_gui


def main():
    """Main application entry point."""
    # If running windowless (pythonw), redirect stdout/stderr to avoid issues
    if not sys.stdout.isatty() or 'pythonw' in sys.executable.lower():
        # Redirect to null device for windowless operation
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    else:
        print("Starting Spending Tracker GUI...")

    try:
        # Launch the PySide6 GUI
        return run_gui()
    except ImportError as e:
        print("Error: Missing required dependencies.")
        print(f"Details: {e}")
        print()
        print("Please ensure you have installed all dependencies:")
        print("pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
