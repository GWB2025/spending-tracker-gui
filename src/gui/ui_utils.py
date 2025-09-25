#!/usr/bin/env python3
"""
UI Utilities for Spending Tracker GUI

This module contains utility functions and classes to eliminate code repetition
and improve maintainability of the GUI components.
"""

from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QLineEdit,
    QLabel,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt


class UIStyleManager:
    """Manages consistent styling across the application."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.colors = config.get("ui", {}).get("colors", {})

    def get_primary_button_style(self) -> str:
        """Get consistent primary button styling."""
        return (
            f"background-color: {self.colors.get('primary', '#007acc')}; "
            "color: white; "
            "padding: 8px; "
            "font-weight: bold;"
        )

    def get_success_button_style(self) -> str:
        """Get consistent success button styling."""
        return (
            f"background-color: {self.colors.get('success', '#28a745')}; "
            "color: white; "
            "padding: 8px; "
            "font-weight: bold;"
        )

    def get_warning_button_style(self) -> str:
        """Get consistent warning button styling."""
        return (
            f"background-color: {self.colors.get('warning', '#ffc107')}; "
            "color: black; "
            "padding: 8px; "
            "font-weight: bold;"
        )

    def get_danger_button_style(self) -> str:
        """Get consistent danger button styling."""
        return (
            f"background-color: {self.colors.get('danger', '#dc3545')}; "
            "color: white; "
            "padding: 8px; "
            "font-weight: bold;"
        )

    def get_info_text_style(self) -> str:
        """Get consistent info text styling."""
        return "color: #666; font-style: italic; margin-bottom: 10px;"


class FormFieldFactory:
    """Factory for creating consistent form fields."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def create_text_field(
        self,
        placeholder: str = "",
        tooltip: str = "",
        enable_copy_paste: bool = True,
    ) -> QLineEdit:
        """Create a standardized text input field."""
        field = QLineEdit()
        if placeholder:
            field.setPlaceholderText(placeholder)
        if tooltip:
            enhanced_tooltip = (
                f"{tooltip}. Supports Ctrl+C/V for copy/paste."
                if enable_copy_paste
                else tooltip
            )
            field.setToolTip(enhanced_tooltip)
        if enable_copy_paste:
            field.setContextMenuPolicy(Qt.DefaultContextMenu)
        return field

    def create_password_field(
        self, placeholder: str = "", tooltip: str = ""
    ) -> QLineEdit:
        """Create a standardized password input field."""
        field = self.create_text_field(placeholder, tooltip)
        field.setEchoMode(QLineEdit.Password)
        return field

    def create_currency_spin_box(
        self, min_value: float = 0.01, max_value: float = 999999.99
    ) -> QDoubleSpinBox:
        """Create a standardized currency input field."""
        spin_box = QDoubleSpinBox()
        spin_box.setRange(min_value, max_value)
        spin_box.setDecimals(2)
        spin_box.setPrefix(self.config["data"]["currency"]["symbol"])
        return spin_box

    def create_editable_combo_box(
        self, items: List[str], tooltip: str = ""
    ) -> QComboBox:
        """Create a standardized editable combo box."""
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(items)
        if tooltip:
            combo.setToolTip(tooltip)
        return combo

    def create_standard_button(
        self,
        text: str,
        style_type: str = "primary",
        tooltip: str = "",
        style_manager: Optional[UIStyleManager] = None,
    ) -> QPushButton:
        """Create a standardized button with consistent styling."""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)

        if style_manager:
            style_map = {
                "primary": style_manager.get_primary_button_style,
                "success": style_manager.get_success_button_style,
                "warning": style_manager.get_warning_button_style,
                "danger": style_manager.get_danger_button_style,
            }
            style_func = style_map.get(style_type)
            if style_func:
                button.setStyleSheet(style_func())

        return button


class MessageManager:
    """Manages consistent messaging across the application."""

    @staticmethod
    def show_success(parent, title: str, message: str):
        """Show success message dialog."""
        QMessageBox.information(parent, title, f"✅ {message}")

    @staticmethod
    def show_error(parent, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.warning(parent, title, f"❌ {message}")

    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Show warning message dialog."""
        QMessageBox.warning(parent, title, f"⚠️ {message}")

    @staticmethod
    def show_info(parent, title: str, message: str):
        """Show info message dialog."""
        QMessageBox.information(parent, title, f"ℹ️ {message}")

    @staticmethod
    def confirm_action(
        parent, title: str, message: str, default_no: bool = True
    ) -> bool:
        """Show confirmation dialog and return user choice."""
        flags = QMessageBox.Yes | QMessageBox.No
        default = QMessageBox.No if default_no else QMessageBox.Yes
        reply = QMessageBox.question(parent, title, message, flags, default)
        return reply == QMessageBox.Yes


class ValidationHelper:
    """Helper class for common validation tasks."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format."""
        return "@" in email and "." in email.split("@")[-1]

    @staticmethod
    def validate_positive_amount(amount: float) -> bool:
        """Validate that amount is positive."""
        return amount > 0

    @staticmethod
    def validate_non_empty_string(text: str) -> bool:
        """Validate that string is not empty after stripping."""
        return bool(text.strip())

    @staticmethod
    def format_currency_amount(amount: float, symbol: str = "£") -> str:
        """Format amount with currency symbol."""
        return f"{symbol}{amount:.2f}"


class LayoutHelper:
    """Helper class for common layout operations."""

    @staticmethod
    def create_form_row(
        layout: QGridLayout,
        row: int,
        label_text: str,
        widget,
        tooltip: str = "",
    ):
        """Add a labeled widget to a grid layout."""
        label = QLabel(label_text)
        if tooltip:
            label.setToolTip(tooltip)
            widget.setToolTip(tooltip)
        layout.addWidget(label, row, 0)
        layout.addWidget(widget, row, 1)

    @staticmethod
    def create_button_row(buttons: List[QPushButton], add_stretch: bool = True):
        """Create a horizontal layout with buttons."""
        layout = QHBoxLayout()
        for button in buttons:
            layout.addWidget(button)
        if add_stretch:
            layout.addStretch()
        return layout
