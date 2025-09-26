#!/usr/bin/env python3
"""
Splash Screen for Spending Tracker GUI

Shows a quick loading screen while the main application initializes.
"""

from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor


class SpendingTrackerSplashScreen(QSplashScreen):
    """Simple splash screen for the Spending Tracker application."""

    def __init__(self):
        # Create a simple pixmap for the splash screen
        pixmap = QPixmap(400, 200)
        pixmap.fill(QColor(70, 130, 180))  # Steel blue background

        # Draw text on the pixmap
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))  # White text

        # Title font
        title_font = QFont("Arial", 18, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(50, 80, "Spending Tracker")

        # Subtitle font
        subtitle_font = QFont("Arial", 10)
        painter.setFont(subtitle_font)
        painter.drawText(50, 110, "Loading application...")

        painter.end()

        super().__init__(pixmap)

        # Center the splash screen
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

    def show_message(self, message):
        """Show a message on the splash screen."""
        self.showMessage(message, Qt.AlignBottom | Qt.AlignLeft, QColor(255, 255, 255))

    def close_splash(self):
        """Close the splash screen."""
        self.close()


def show_splash_screen():
    """Create and show the splash screen."""
    splash = SpendingTrackerSplashScreen()
    splash.show()
    splash.show_message("Initialising...")
    return splash
