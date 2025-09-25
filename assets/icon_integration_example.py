#!/usr/bin/env python3
"""
Icon Integration Example for Spending Tracker GUI

This file demonstrates how to use the custom icons in your PySide6 application.
Copy the relevant code sections into your main_window.py or other GUI modules.
"""

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon, QPixmap
from pathlib import Path
import sys


def get_icon_path(icon_name: str) -> str:
    """
    Get the path to an icon file.
    
    Args:
        icon_name: Name of the icon file (e.g., 'app_icon.png', 'spending_tracker_icon.ico')
    
    Returns:
        Full path to the icon file
    """
    assets_dir = Path(__file__).parent
    return str(assets_dir / icon_name)


def setup_application_icon(app: QApplication):
    """
    Set up the application icon that appears in the taskbar and window title bar.
    Call this after creating your QApplication instance.
    
    Args:
        app: The QApplication instance
    """
    # Use the ICO file for Windows compatibility
    icon_path = get_icon_path('spending_tracker_icon.ico')
    app.setWindowIcon(QIcon(icon_path))


def setup_window_icon(window: QMainWindow):
    """
    Set up the window icon for a specific window.
    
    Args:
        window: The QMainWindow instance
    """
    # Use PNG for better quality in window
    icon_path = get_icon_path('app_icon.png')
    window.setWindowIcon(QIcon(icon_path))


class ExampleMainWindow(QMainWindow):
    """Example of how to integrate the icon into your main window class."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spending Tracker - Personal Finance Manager")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set the window icon
        self.set_window_icon()
        
    def set_window_icon(self):
        """Set the custom icon for this window."""
        icon_path = get_icon_path('app_icon.png')
        self.setWindowIcon(QIcon(icon_path))
        
        # You can also use different sizes for different contexts:
        # Small icon for system tray (if you use one):
        # small_icon_path = get_icon_path('spending_tracker_icon_16x16.png')
        # 
        # Medium icon for toolbar buttons:
        # medium_icon_path = get_icon_path('spending_tracker_icon_32x32.png')


def main():
    """Example of complete application setup with custom icons."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Spending Tracker")
    app.setApplicationDisplayName("Spending Tracker - Personal Finance Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Your Organisation")
    app.setOrganizationDomain("yourwebsite.co.uk")  # British domain
    
    # Set up the application icon (appears in taskbar, Alt+Tab, etc.)
    setup_application_icon(app)
    
    # Create and show the main window
    window = ExampleMainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    """
    This is just an example. In your actual application, you would integrate
    the icon setup code into your existing main.py and main_window.py files.
    """
    print("This is an example file showing how to use the custom icons.")
    print("To actually run your application, use: python src/main.py")
    
    # Uncomment the line below to run the example:
    # sys.exit(main())


# Example integration for your existing main_window.py:
"""
In your src/gui/main_window.py, you might add something like this:

from pathlib import Path
from PySide6.QtGui import QIcon

def get_icon_path():
    # Navigate to assets directory from gui directory
    assets_dir = Path(__file__).parent.parent.parent / 'assets'
    return str(assets_dir / 'app_icon.png')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spending Tracker - Personal Finance Manager")
        
        # Set custom icon
        icon_path = get_icon_path()
        self.setWindowIcon(QIcon(icon_path))
        
        # Rest of your existing initialisation code...
"""