#!/usr/bin/env python3
"""
Spending Tracker GUI - Windowless Launcher

This .pyw file launches the Spending Tracker GUI without showing a console window.
"""

import sys
import os
from pathlib import Path

def main():
    # Change to the application directory
    app_dir = Path(__file__).parent
    os.chdir(str(app_dir))
    
    # Check if we're running from the virtual environment
    venv_python = app_dir / "venv" / "Scripts" / "pythonw.exe"
    
    if venv_python.exists() and "venv" not in sys.executable:
        # Not running from venv - restart with virtual environment's pythonw
        import subprocess
        try:
            # Use CREATE_NO_WINDOW flag to prevent console window
            subprocess.Popen(
                [str(venv_python), str(app_dir / "src" / "main.py")],
                cwd=str(app_dir),
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return
        except Exception as e:
            show_error(f"Failed to launch with virtual environment: {e}")
            return
    
    # Running from venv or venv not found - try direct launch
    try:
        # Add the project root to the Python path
        sys.path.insert(0, str(app_dir))
        
        # Import and run the main application
        from src.gui.main_window import main as run_gui
        sys.exit(run_gui())
        
    except ImportError as e:
        show_error(f"Missing dependencies: {e}\n\nPlease install requirements:\npip install -r requirements.txt")
    except Exception as e:
        show_error(f"Failed to start Spending Tracker: {e}")

def show_error(message):
    """Show error message using tkinter."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        messagebox.showerror("Spending Tracker Error", message)
        root.destroy()
    except:
        # Fallback if tkinter fails
        pass

if __name__ == "__main__":
    main()
