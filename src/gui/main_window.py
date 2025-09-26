#!/usr/bin/env python3
"""
Main Window for Spending Tracker GUI

This module contains the main application window and primary UI components.
"""

import sys
from pathlib import Path

# Essential Qt imports for main window - other widgets imported as needed
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QDateEdit,
    QLabel,
    QMessageBox,
    QMenu,
    QDialog,
    QLineEdit,  # Common widgets used across methods
)
from PySide6.QtCore import Qt, QDate, QTimer

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import only essential components immediately
from src.config.config_manager import ConfigManager


class SpendingTrackerMainWindow(QMainWindow):
    """Main window for the Spending Tracker application."""

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()

        # Lazy-loaded components (initialized when needed)
        self._expense_controller = None
        self._email_service = None
        self._email_scheduler = None
        self.use_mock_data = False

        # Initialize UI first for fast display
        self.init_ui()

        # Defer heavy initialization to after UI is shown
        self.initialization_timer = QTimer()
        self.initialization_timer.setSingleShot(True)
        self.initialization_timer.timeout.connect(self._complete_initialization)
        self.initialization_timer.start(100)  # Initialize after 100ms

    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle(self.config["app"]["window"]["title"])
        self.setGeometry(
            100,
            100,
            self.config["app"]["window"]["width"],
            self.config["app"]["window"]["height"],
        )

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_expense_entry_tab()
        self.create_expense_list_tab()
        self.create_summary_tab()
        self.create_settings_tab()
        self.create_email_settings_tab()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Welcome to Spending Tracker!")

        # Load saved settings after UI is fully created
        self.load_saved_settings()

    def create_expense_entry_tab(self):
        """Create the expense entry tab."""
        # Import widgets only when creating this tab
        from PySide6.QtWidgets import (
            QHBoxLayout,
            QGroupBox,
            QGridLayout,
            QLabel,
            QDateEdit,
            QDoubleSpinBox,
            QComboBox,
            QLineEdit,
            QCheckBox,
            QPushButton,
        )

        expense_tab = QWidget()
        layout = QVBoxLayout(expense_tab)

        # Create expense entry form
        form_group = QGroupBox("Add New Transaction")
        form_layout = QGridLayout(form_group)

        # Date input
        form_layout.addWidget(QLabel("Date:"), 0, 0)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setToolTip(
            "Select the date when this expense occurred. Click the calendar icon to open date picker."
        )
        form_layout.addWidget(self.date_edit, 0, 1)

        # Amount input
        form_layout.addWidget(QLabel("Amount:"), 1, 0)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix(self.config["data"]["currency"]["symbol"])
        self.amount_spin.setToolTip(
            "Enter the amount spent. Use decimal point for pence/cents (e.g., 12.50). Currency can be changed in Settings."
        )
        form_layout.addWidget(self.amount_spin, 1, 1)

        # Category input
        form_layout.addWidget(QLabel("Category:"), 2, 0)
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.config["data"]["default_categories"])
        self.category_combo.setToolTip(
            "Select an existing category or type a new one. Categories help organize your spending for better analysis."
        )
        form_layout.addWidget(self.category_combo, 2, 1)

        # Description input
        form_layout.addWidget(QLabel("Description:"), 3, 0)
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Enter expense description...")
        self.description_edit.setToolTip(
            "Optional: Add details about this expense (e.g., 'Lunch at Café', 'Petrol for car', 'Weekly groceries'). Supports Ctrl+C/V for copy/paste."
        )
        # Ensure copy/paste context menu is enabled
        self.description_edit.setContextMenuPolicy(Qt.DefaultContextMenu)
        form_layout.addWidget(self.description_edit, 3, 1)

        # Credit/Income checkbox
        self.credit_checkbox = QCheckBox("This is a credit/income")
        self.credit_checkbox.setToolTip(
            "Check this if you're adding income or a credit (will appear as positive amount)."
        )
        form_layout.addWidget(self.credit_checkbox, 4, 0, 1, 2)

        # Recurring expense checkbox
        self.recurring_expense_checkbox = QCheckBox(
            "Make this a recurring monthly expense"
        )
        self.recurring_expense_checkbox.setToolTip(
            "Check this to automatically add this expense every month on the same date."
        )
        form_layout.addWidget(self.recurring_expense_checkbox, 5, 0, 1, 2)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_expense_btn = QPushButton("Add Transaction")
        self.add_expense_btn.setStyleSheet(
            f"background-color: {self.config['ui']['colors']['primary']}; color: white; padding: 8px;"
        )
        self.add_expense_btn.setToolTip(
            "Save this transaction to your records. All fields except description are required."
        )
        self.clear_form_btn = QPushButton("Clear Form")
        self.clear_form_btn.setToolTip(
            "Reset all fields to their default values to start entering a new expense."
        )

        button_layout.addWidget(self.add_expense_btn)
        button_layout.addWidget(self.clear_form_btn)
        button_layout.addStretch()

        # Add to layout
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addStretch()

        self.tab_widget.addTab(expense_tab, "Add Transaction")

    def create_expense_list_tab(self):
        """Create the expense list tab."""
        # Import widgets only when creating this tab
        from PySide6.QtWidgets import QHBoxLayout, QTableWidget, QPushButton, QGroupBox

        list_tab = QWidget()
        layout = QVBoxLayout(list_tab)

        # Controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip(
            "Reload the expense list to show any recent changes or new data."
        )
        export_btn = QPushButton("Export to CSV")
        export_btn.setToolTip(
            "Export all your expenses to a CSV file that can be opened in Excel or other spreadsheet applications."
        )

        # Connect buttons to methods
        refresh_btn.clicked.connect(self.refresh_data)
        export_btn.clicked.connect(self.export_csv)

        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(export_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Expense table
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(4)
        self.expense_table.setHorizontalHeaderLabels(
            ["Date", "Amount", "Category", "Description"]
        )
        self.expense_table.setToolTip(
            "Your transaction history (expenses and credits). Most recent transactions appear at the top. Double-click a transaction to edit it, or right-click for more options."
        )

        # Enable selection of entire rows
        self.expense_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.expense_table.setSelectionMode(QTableWidget.SingleSelection)

        # Enable context menu and double-click editing
        self.expense_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.expense_table.customContextMenuRequested.connect(
            self.show_expense_context_menu
        )
        self.expense_table.itemDoubleClicked.connect(self.edit_selected_expense)

        # Set table properties
        header = self.expense_table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.expense_table)

        self.tab_widget.addTab(list_tab, "Transaction History")

    def create_summary_tab(self):
        """Create the summary/dashboard tab."""
        # Import widgets only when creating this tab
        from PySide6.QtWidgets import QHBoxLayout, QGroupBox, QLabel

        summary_tab = QWidget()
        layout = QVBoxLayout(summary_tab)

        # Summary cards
        cards_layout = QHBoxLayout()

        # Total income card
        income_card = QGroupBox("Total Income")
        income_card.setToolTip("Total income and credits received.")
        income_layout = QVBoxLayout(income_card)
        self.income_label = QLabel("$0.00")
        self.income_label.setAlignment(Qt.AlignCenter)
        self.income_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #28a745;"
        )
        self.income_label.setToolTip("Total income and credits received.")
        income_layout.addWidget(self.income_label)

        # Total expenses card
        expenses_card = QGroupBox("Total Expenses")
        expenses_card.setToolTip("Total amount spent on all expenses.")
        expenses_layout = QVBoxLayout(expenses_card)
        self.expenses_label = QLabel("$0.00")
        self.expenses_label.setAlignment(Qt.AlignCenter)
        self.expenses_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #dc3545;"
        )
        self.expenses_label.setToolTip("Total amount spent on all expenses.")
        expenses_layout.addWidget(self.expenses_label)

        # Net balance card
        balance_card = QGroupBox("Net Balance")
        balance_card.setToolTip("Net balance (income minus expenses).")
        balance_layout = QVBoxLayout(balance_card)
        self.balance_label = QLabel("$0.00")
        self.balance_label.setAlignment(Qt.AlignCenter)
        self.balance_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #007acc;"
        )
        self.balance_label.setToolTip("Net balance (income minus expenses).")
        balance_layout.addWidget(self.balance_label)

        cards_layout.addWidget(income_card)
        cards_layout.addWidget(expenses_card)
        cards_layout.addWidget(balance_card)

        layout.addLayout(cards_layout)

        # Placeholder for charts
        chart_group = QGroupBox("Spending Analysis")
        chart_layout = QVBoxLayout(chart_group)
        chart_placeholder = QLabel(
            "Charts will be displayed here\n(Integration with matplotlib/plotly)"
        )
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setStyleSheet(
            "color: #666; font-style: italic; padding: 50px;"
        )
        chart_layout.addWidget(chart_placeholder)

        layout.addWidget(chart_group)

        self.tab_widget.addTab(summary_tab, "Summary")

    def create_settings_tab(self):
        """Create the settings tab."""
        # Import widgets only when creating this tab
        from PySide6.QtWidgets import (
            QGridLayout,
            QGroupBox,
            QLabel,
            QComboBox,
            QPushButton,
            QLineEdit,
            QSpinBox,
        )

        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)

        # Data Source settings
        data_group = QGroupBox("Data Source")
        data_layout = QGridLayout(data_group)

        data_layout.addWidget(QLabel("Data Source:"), 0, 0)
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["Mock Data (Local)", "Google Sheets"])
        self.data_source_combo.setCurrentIndex(0 if self.use_mock_data else 1)
        self.data_source_combo.setToolTip(
            "Choose where to store your expense data:\n• Mock Data: Local storage, fast and private\n• Google Sheets: Cloud storage, sync across devices"
        )
        data_layout.addWidget(self.data_source_combo, 0, 1)

        # Status indicator
        self.connection_status = QLabel("Status: Google Sheets selected")
        self.connection_status.setStyleSheet("color: #007acc; font-weight: bold;")
        data_layout.addWidget(self.connection_status, 1, 0, 1, 2)

        layout.addWidget(data_group)

        # Google Sheets settings
        sheets_group = QGroupBox("Google Sheets Configuration")
        sheets_layout = QGridLayout(sheets_group)

        sheets_layout.addWidget(QLabel("Spreadsheet ID:"), 0, 0)
        self.spreadsheet_id_edit = QLineEdit()
        self.spreadsheet_id_edit.setText(
            self.config.get("google_sheets", {}).get("spreadsheet_id", "")
        )
        self.spreadsheet_id_edit.setPlaceholderText("Enter your Google Sheets ID...")
        self.spreadsheet_id_edit.setToolTip(
            "The ID from your Google Sheets URL. See docs/google_sheets_setup.md for setup instructions."
        )
        sheets_layout.addWidget(self.spreadsheet_id_edit, 0, 1)

        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.setToolTip(
            "Check if the app can connect to your Google Sheets. Requires setup first."
        )
        sheets_layout.addWidget(self.test_connection_btn, 1, 0)

        self.sync_now_btn = QPushButton("Sync Now")
        self.sync_now_btn.setToolTip(
            "Upload local data to Google Sheets or download changes from the cloud."
        )
        sheets_layout.addWidget(self.sync_now_btn, 1, 1)

        self.save_spreadsheet_id_btn = QPushButton("Save Spreadsheet ID")
        self.save_spreadsheet_id_btn.setToolTip(
            "Save the entered Spreadsheet ID to your configuration."
        )
        sheets_layout.addWidget(self.save_spreadsheet_id_btn, 2, 0)

        layout.addWidget(sheets_group)

        # Google Sheets Setup Status panel
        status_group = QGroupBox("Google Sheets Setup Status")
        status_layout = QGridLayout(status_group)

        # Status labels
        status_layout.addWidget(QLabel("Spreadsheet ID:"), 0, 0)
        self.spreadsheet_status = QLabel("❌ Not set")
        self.spreadsheet_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        status_layout.addWidget(self.spreadsheet_status, 0, 1)

        status_layout.addWidget(QLabel("Credentials File:"), 1, 0)
        self.credentials_status = QLabel("❌ Missing")
        self.credentials_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        status_layout.addWidget(self.credentials_status, 1, 1)

        status_layout.addWidget(QLabel("Token File:"), 2, 0)
        self.token_status = QLabel("❌ Missing")
        self.token_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        status_layout.addWidget(self.token_status, 2, 1)

        # Setup actions
        self.refresh_status_btn = QPushButton("Refresh Status")
        self.refresh_status_btn.setToolTip(
            "Check current status of Google Sheets setup components."
        )
        status_layout.addWidget(self.refresh_status_btn, 3, 0)

        self.open_setup_guide_btn = QPushButton("Open Setup Guide")
        self.open_setup_guide_btn.setToolTip(
            "Open the detailed Google Sheets setup guide in your default text editor."
        )
        status_layout.addWidget(self.open_setup_guide_btn, 3, 1)

        layout.addWidget(status_group)

        # Mock Data settings
        mock_group = QGroupBox("Mock Data Options")
        mock_layout = QGridLayout(mock_group)

        self.reset_sample_data_btn = QPushButton("Reset to Sample Data")
        self.reset_sample_data_btn.setToolTip(
            "Replace all current data with 50 realistic sample expenses for testing and demo purposes."
        )
        self.clear_all_data_btn = QPushButton("Factory Reset")
        self.clear_all_data_btn.setToolTip(
            "⚠️ FACTORY RESET: Permanently delete ALL data and reset app to fresh state. This cannot be undone! (Mock Data mode only)"
        )
        self.clear_all_data_btn.setStyleSheet(
            "background-color: #dc3545; color: white; font-weight: bold; padding: 8px;"
        )
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.setToolTip(
            "Save all your expenses to a CSV file for backup or analysis in Excel/Google Sheets."
        )

        mock_layout.addWidget(self.reset_sample_data_btn, 0, 0)
        mock_layout.addWidget(self.clear_all_data_btn, 0, 1)
        mock_layout.addWidget(self.export_csv_btn, 1, 0)

        layout.addWidget(mock_group)

        # Theme settings
        theme_group = QGroupBox("Appearance")
        theme_layout = QGridLayout(theme_group)

        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        self.theme_combo.setToolTip(
            "Choose the visual theme (currently Light theme only - Dark theme coming soon)."
        )
        theme_layout.addWidget(self.theme_combo, 0, 1)

        layout.addWidget(theme_group)

        # Currency settings
        currency_group = QGroupBox("Currency")
        currency_layout = QGridLayout(currency_group)

        currency_layout.addWidget(QLabel("Currency:"), 0, 0)
        self.currency_combo = QComboBox()
        self.load_currencies()
        self.currency_combo.setToolTip(
            "Select your preferred currency. Changes the symbol shown in amount fields and summaries."
        )
        currency_layout.addWidget(self.currency_combo, 0, 1)

        self.save_currency_btn = QPushButton("Save Currency")
        self.save_currency_btn.setToolTip(
            "Apply the selected currency and save it to your settings."
        )
        currency_layout.addWidget(self.save_currency_btn, 1, 0)

        layout.addWidget(currency_group)

        # Recurring Expenses management
        expenses_group = QGroupBox("Recurring Expenses Management")
        expenses_layout = QGridLayout(expenses_group)

        # Info label
        info_label = QLabel(
            "📅 Recurring transactions are created when you check 'Make this a recurring monthly expense' when adding expenses or credits."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "color: #666; font-style: italic; margin-bottom: 10px;"
        )
        expenses_layout.addWidget(info_label, 0, 0, 1, 2)

        # View recurring expenses button
        self.view_recurring_btn = QPushButton("View Recurring Expenses")
        self.view_recurring_btn.setToolTip(
            "View and manage all your recurring monthly expenses."
        )
        expenses_layout.addWidget(self.view_recurring_btn, 1, 0)

        # Process all recurring expenses button
        self.process_all_recurring_btn = QPushButton("Process All Due Expenses")
        self.process_all_recurring_btn.setToolTip(
            "Manually process all recurring expenses that are due for this month."
        )
        expenses_layout.addWidget(self.process_all_recurring_btn, 1, 1)

        layout.addWidget(expenses_group)
        layout.addStretch()

        self.tab_widget.addTab(settings_tab, "Settings")

    def create_email_settings_tab(self):
        """Create the email settings tab."""
        # Import widgets only when creating this tab
        from PySide6.QtWidgets import (
            QGridLayout,
            QGroupBox,
            QLabel,
            QLineEdit,
            QSpinBox,
            QPushButton,
            QHBoxLayout,
            QCheckBox,
            QListWidget,
        )

        email_tab = QWidget()
        layout = QVBoxLayout(email_tab)

        # Email Configuration
        email_config_group = QGroupBox("Email Configuration")
        email_config_layout = QGridLayout(email_config_group)

        # SMTP Server
        email_config_layout.addWidget(QLabel("SMTP Server:"), 0, 0)
        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText("e.g., smtp.gmail.com")
        self.smtp_server_edit.setToolTip(
            "Your email provider's SMTP server address. Supports Ctrl+C/V for copy/paste."
        )
        self.smtp_server_edit.setContextMenuPolicy(Qt.DefaultContextMenu)
        email_config_layout.addWidget(self.smtp_server_edit, 0, 1)

        # SMTP Port
        email_config_layout.addWidget(QLabel("SMTP Port:"), 1, 0)
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        self.smtp_port_spin.setToolTip(
            "SMTP port number (587 for TLS, 465 for SSL, 25 for unencrypted)"
        )
        email_config_layout.addWidget(self.smtp_port_spin, 1, 1)

        # Username
        email_config_layout.addWidget(QLabel("Username:"), 2, 0)
        self.email_username_edit = QLineEdit()
        self.email_username_edit.setPlaceholderText("your.email@example.com")
        self.email_username_edit.setToolTip(
            "Your email address for authentication. Supports Ctrl+C/V for copy/paste."
        )
        self.email_username_edit.setContextMenuPolicy(Qt.DefaultContextMenu)
        email_config_layout.addWidget(self.email_username_edit, 2, 1)

        # Password with enhanced features
        email_config_layout.addWidget(QLabel("Password:"), 3, 0)

        # Create password container with toggle button
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(2)

        self.email_password_edit = QLineEdit()
        self.email_password_edit.setEchoMode(QLineEdit.Password)
        self.email_password_edit.setPlaceholderText(
            "16-character app password (spaces auto-removed)"
        )
        self.email_password_edit.setToolTip(
            "Gmail App Password (16 characters). Spaces will be automatically removed.\n"
            "Format: abcd efgh ijkl mnop → abcdefghijklmnop"
        )
        self.email_password_edit.setContextMenuPolicy(Qt.DefaultContextMenu)

        # Connect text change event for validation and formatting
        self.email_password_edit.textChanged.connect(self.on_password_text_changed)

        # Create show/hide password toggle button
        self.password_toggle_btn = QPushButton()
        self.password_toggle_btn.setFixedSize(30, 25)
        self.password_toggle_btn.setFlat(True)
        self.password_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.password_toggle_btn.setText("👁")
        self.password_toggle_btn.setToolTip("Click to show/hide password")
        self.password_toggle_btn.clicked.connect(self.toggle_password_visibility)
        self.password_toggle_btn.setStyleSheet(
            "QPushButton { border: 1px solid #ccc; border-radius: 3px; background: #f8f9fa; }"
            "QPushButton:hover { background: #e9ecef; }"
            "QPushButton:pressed { background: #dee2e6; }"
        )

        # Add validation status indicator
        self.password_status_label = QLabel()
        self.password_status_label.setFixedSize(20, 25)
        self.password_status_label.setAlignment(Qt.AlignCenter)

        password_layout.addWidget(self.email_password_edit)
        password_layout.addWidget(self.password_toggle_btn)
        password_layout.addWidget(self.password_status_label)

        email_config_layout.addWidget(password_container, 3, 1)

        # From Name
        email_config_layout.addWidget(QLabel("From Name:"), 4, 0)
        self.from_name_edit = QLineEdit()
        self.from_name_edit.setText("Spending Tracker")
        self.from_name_edit.setToolTip(
            "Display name that appears in the 'From' field of emails"
        )
        email_config_layout.addWidget(self.from_name_edit, 4, 1)

        # Use TLS checkbox
        self.use_tls_checkbox = QCheckBox("Use TLS encryption")
        self.use_tls_checkbox.setChecked(True)
        self.use_tls_checkbox.setToolTip(
            "Enable TLS encryption (recommended for most email providers)"
        )
        email_config_layout.addWidget(self.use_tls_checkbox, 5, 0, 1, 2)

        # Test connection button
        self.test_email_btn = QPushButton("Test Email Connection")
        self.test_email_btn.setToolTip(
            "Test the email configuration by attempting to connect and authenticate"
        )
        email_config_layout.addWidget(self.test_email_btn, 6, 0)

        # Save email settings button
        self.save_email_settings_btn = QPushButton("Save Email Settings")
        self.save_email_settings_btn.setToolTip(
            "Save the email configuration to use for sending reports"
        )
        email_config_layout.addWidget(self.save_email_settings_btn, 6, 1)

        layout.addWidget(email_config_group)

        # Email Recipients
        recipients_group = QGroupBox("Email Recipients")
        recipients_layout = QVBoxLayout(recipients_group)

        # Recipients list
        recipients_list_layout = QHBoxLayout()
        self.recipients_list = QListWidget()
        self.recipients_list.setToolTip(
            "List of email addresses that will receive monthly reports"
        )
        recipients_list_layout.addWidget(self.recipients_list)

        # Recipients buttons
        recipients_buttons_layout = QVBoxLayout()
        self.add_recipient_btn = QPushButton("Add")
        self.add_recipient_btn.setToolTip("Add a new email recipient")
        self.remove_recipient_btn = QPushButton("Remove")
        self.remove_recipient_btn.setToolTip("Remove selected recipient")
        recipients_buttons_layout.addWidget(self.add_recipient_btn)
        recipients_buttons_layout.addWidget(self.remove_recipient_btn)
        recipients_buttons_layout.addStretch()

        recipients_list_layout.addLayout(recipients_buttons_layout)
        recipients_layout.addLayout(recipients_list_layout)

        # Add recipient input
        add_recipient_layout = QHBoxLayout()
        add_recipient_layout.addWidget(QLabel("New recipient:"))
        self.new_recipient_edit = QLineEdit()
        self.new_recipient_edit.setPlaceholderText("email@example.com")
        self.new_recipient_edit.setToolTip(
            "Enter an email address to add to the recipient list. Supports Ctrl+C/V for copy/paste."
        )
        self.new_recipient_edit.setContextMenuPolicy(Qt.DefaultContextMenu)
        add_recipient_layout.addWidget(self.new_recipient_edit)
        recipients_layout.addLayout(add_recipient_layout)

        layout.addWidget(recipients_group)

        # Scheduling Settings
        schedule_group = QGroupBox("Email Schedule Settings")
        schedule_layout = QGridLayout(schedule_group)

        # Enable scheduling checkbox
        self.enable_scheduling_checkbox = QCheckBox("Enable automatic monthly reports")
        self.enable_scheduling_checkbox.setToolTip(
            "Automatically send expense summaries on a monthly schedule"
        )
        schedule_layout.addWidget(self.enable_scheduling_checkbox, 0, 0, 1, 2)

        # Day of month
        schedule_layout.addWidget(QLabel("Day of Month:"), 1, 0)
        self.schedule_day_spin = QSpinBox()
        self.schedule_day_spin.setRange(1, 28)
        self.schedule_day_spin.setValue(1)
        self.schedule_day_spin.setToolTip(
            "Day of the month to send reports (1-28 to ensure compatibility with all months)"
        )
        schedule_layout.addWidget(self.schedule_day_spin, 1, 1)

        # Time of day
        schedule_layout.addWidget(QLabel("Time:"), 2, 0)
        time_layout = QHBoxLayout()
        self.schedule_hour_spin = QSpinBox()
        self.schedule_hour_spin.setRange(0, 23)
        self.schedule_hour_spin.setValue(9)
        self.schedule_hour_spin.setToolTip("Hour to send reports (24-hour format)")
        time_layout.addWidget(self.schedule_hour_spin)
        time_layout.addWidget(QLabel(":"))
        self.schedule_minute_spin = QSpinBox()
        self.schedule_minute_spin.setRange(0, 59)
        self.schedule_minute_spin.setValue(0)
        self.schedule_minute_spin.setToolTip("Minute to send reports")
        time_layout.addWidget(self.schedule_minute_spin)
        time_layout.addStretch()
        schedule_layout.addLayout(time_layout, 2, 1)

        # Subject prefix
        schedule_layout.addWidget(QLabel("Subject Prefix:"), 3, 0)
        self.subject_prefix_edit = QLineEdit()
        self.subject_prefix_edit.setText("[Monthly Report] ")
        self.subject_prefix_edit.setToolTip(
            "Text to add at the beginning of email subjects"
        )
        schedule_layout.addWidget(self.subject_prefix_edit, 3, 1)

        # Include CSV attachment checkbox
        self.include_csv_checkbox = QCheckBox("Include CSV attachment")
        self.include_csv_checkbox.setChecked(True)
        self.include_csv_checkbox.setToolTip(
            "Attach a CSV file with detailed expense data"
        )
        schedule_layout.addWidget(self.include_csv_checkbox, 4, 0, 1, 2)

        # Schedule status
        self.schedule_status_label = QLabel("Status: Scheduling disabled")
        self.schedule_status_label.setStyleSheet("color: #666; font-style: italic;")
        schedule_layout.addWidget(self.schedule_status_label, 5, 0, 1, 2)

        # Schedule buttons
        schedule_buttons_layout = QHBoxLayout()
        self.save_schedule_btn = QPushButton("Save Schedule")
        self.save_schedule_btn.setToolTip(
            "Save scheduling settings and start/update the email scheduler"
        )
        self.start_scheduler_btn = QPushButton("Start Scheduler")
        self.start_scheduler_btn.setToolTip("Start the automatic email scheduler")
        self.stop_scheduler_btn = QPushButton("Stop Scheduler")
        self.stop_scheduler_btn.setToolTip("Stop the automatic email scheduler")
        schedule_buttons_layout.addWidget(self.save_schedule_btn)
        schedule_buttons_layout.addWidget(self.start_scheduler_btn)
        schedule_buttons_layout.addWidget(self.stop_scheduler_btn)
        schedule_buttons_layout.addStretch()
        schedule_layout.addLayout(schedule_buttons_layout, 6, 0, 1, 2)

        layout.addWidget(schedule_group)

        # Manual Email Actions
        manual_group = QGroupBox("Manual Email Actions")
        manual_layout = QVBoxLayout(manual_group)

        # Send buttons
        manual_buttons_layout = QHBoxLayout()
        self.send_monthly_btn = QPushButton("Send Last Month's Report")
        self.send_monthly_btn.setToolTip(
            "Send a monthly report for the previous month immediately"
        )
        self.send_test_email_btn = QPushButton("Send Test Email")
        self.send_test_email_btn.setToolTip(
            "Send a test email with current month's summary"
        )
        manual_buttons_layout.addWidget(self.send_monthly_btn)
        manual_buttons_layout.addWidget(self.send_test_email_btn)
        manual_buttons_layout.addStretch()

        manual_layout.addLayout(manual_buttons_layout)

        # Custom date range
        custom_range_layout = QHBoxLayout()
        custom_range_layout.addWidget(QLabel("Custom Range:"))
        self.custom_start_date = QDateEdit()
        self.custom_start_date.setCalendarPopup(True)
        self.custom_start_date.setDate(QDate.currentDate().addDays(-30))
        self.custom_start_date.setToolTip("Start date for custom report")
        custom_range_layout.addWidget(self.custom_start_date)
        custom_range_layout.addWidget(QLabel("to"))
        self.custom_end_date = QDateEdit()
        self.custom_end_date.setCalendarPopup(True)
        self.custom_end_date.setDate(QDate.currentDate())
        self.custom_end_date.setToolTip("End date for custom report")
        custom_range_layout.addWidget(self.custom_end_date)
        self.send_custom_btn = QPushButton("Send Custom Report")
        self.send_custom_btn.setToolTip("Send report for the specified date range")
        custom_range_layout.addWidget(self.send_custom_btn)
        custom_range_layout.addStretch()

        manual_layout.addLayout(custom_range_layout)

        layout.addWidget(manual_group)

        # Load current email settings
        self.load_email_settings()

        layout.addStretch()
        self.tab_widget.addTab(email_tab, "Email Reports")

    def setup_connections(self):
        """Setup signal-slot connections."""
        # Expense form connections
        self.add_expense_btn.clicked.connect(self.add_expense)
        self.clear_form_btn.clicked.connect(self.clear_form)
        self.credit_checkbox.toggled.connect(self.update_form_labels)

        # Settings connections
        self.data_source_combo.currentIndexChanged.connect(self.switch_data_source)
        self.test_connection_btn.clicked.connect(self.test_connection)
        self.sync_now_btn.clicked.connect(self.sync_data)
        self.save_spreadsheet_id_btn.clicked.connect(self.save_spreadsheet_id)

        # Google Sheets status connections
        self.refresh_status_btn.clicked.connect(self.refresh_google_sheets_status)
        self.open_setup_guide_btn.clicked.connect(self.open_setup_guide)

        # Mock data connections
        self.reset_sample_data_btn.clicked.connect(self.reset_sample_data)
        self.clear_all_data_btn.clicked.connect(self.clear_all_data)
        self.export_csv_btn.clicked.connect(self.export_csv)

        # Currency connections
        self.save_currency_btn.clicked.connect(self.save_currency)
        self.currency_combo.currentTextChanged.connect(self.on_currency_changed)

        # Recurring expenses connections
        self.view_recurring_btn.clicked.connect(self.view_recurring_expenses)
        self.process_all_recurring_btn.clicked.connect(
            self.process_all_recurring_expenses
        )

        # Email connections
        self.test_email_btn.clicked.connect(self.test_email_connection)
        self.save_email_settings_btn.clicked.connect(self.save_email_settings)
        self.add_recipient_btn.clicked.connect(self.add_email_recipient)
        self.remove_recipient_btn.clicked.connect(self.remove_email_recipient)
        self.new_recipient_edit.returnPressed.connect(self.add_email_recipient)
        self.save_schedule_btn.clicked.connect(self.save_email_schedule)
        self.start_scheduler_btn.clicked.connect(self.start_email_scheduler)
        self.stop_scheduler_btn.clicked.connect(self.stop_email_scheduler)
        self.send_monthly_btn.clicked.connect(self.send_monthly_report)
        self.send_test_email_btn.clicked.connect(self.send_test_email)
        self.send_custom_btn.clicked.connect(self.send_custom_report)

    def add_expense(self):
        """Add a new expense or credit entry."""
        # Get form data
        date = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_spin.value()
        category = self.category_combo.currentText()
        description = self.description_edit.text()
        is_recurring = self.recurring_expense_checkbox.isChecked()
        is_credit = self.credit_checkbox.isChecked()

        # Validate input
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount.")
            return

        if not category.strip():
            QMessageBox.warning(
                self, "Invalid Input", "Please select or enter a category."
            )
            return

        # Apply sign convention: expenses are negative, credits are positive
        if is_credit:
            amount = abs(amount)  # Ensure it's positive for credits/income
        else:
            amount = -abs(amount)  # Ensure it's negative for expenses

        # Disable button temporarily to prevent double-clicks
        self.add_expense_btn.setEnabled(False)
        self.add_expense_btn.setText("Adding...")

        try:
            # Add transaction using controller
            success, message = self.expense_controller.add_expense(
                date, amount, category, description
            )

            if success:
                # If recurring expense, save it to recurring expenses list
                if is_recurring:
                    self.save_recurring_expense(date, amount, category, description)

                # Auto-sync to Google Sheets if not using mock data
                if not self.use_mock_data:
                    self.add_expense_btn.setText("Syncing...")
                    sync_result = self.expense_controller.sync_data()
                    if not sync_result["success"]:
                        # Show sync warning but don't fail the transaction
                        self.status_bar.showMessage(
                            f"⚠️ Transaction saved but sync failed: "
                            f"{sync_result['message']}"
                        )

                # Show success feedback
                transaction_type = "Credit" if is_credit else "Expense"
                feedback_msg = f"✅ {transaction_type} added successfully"
                if is_recurring:
                    feedback_msg += f" (Saved as recurring {transaction_type.lower()})"
                if not self.use_mock_data:
                    feedback_msg += " and synced to Google Sheets"
                self.show_success_feedback(feedback_msg)

                # Clear form
                self.clear_form()
                # Refresh data displays
                self.refresh_data()
            else:
                transaction_type = "Credit" if is_credit else "Expense"
                QMessageBox.warning(self, f"Error Adding {transaction_type}", message)

        finally:
            # Re-enable button
            self.add_expense_btn.setEnabled(True)
            self.update_form_labels()

    def clear_form(self):
        """Clear the transaction entry form."""
        self.date_edit.setDate(QDate.currentDate())
        self.amount_spin.setValue(0.00)
        self.category_combo.setCurrentText("")
        self.description_edit.clear()
        self.credit_checkbox.setChecked(False)
        self.recurring_expense_checkbox.setChecked(False)
        self.update_form_labels()

    def update_form_labels(self):
        """Update form labels and button text based on credit checkbox state."""
        is_credit = self.credit_checkbox.isChecked()
        if is_credit:
            self.add_expense_btn.setText("Add Credit")
            self.add_expense_btn.setToolTip(
                "Save this credit/income to your records. All fields except description are required."
            )
        else:
            self.add_expense_btn.setText("Add Expense")
            self.add_expense_btn.setToolTip(
                "Save this expense to your records. All fields except description are required."
            )

    def load_initial_data(self):
        """Load initial data into the UI."""
        self.refresh_data()
        # Check for recurring expenses that need processing
        self.check_and_process_recurring_expenses()

    def refresh_data(self):
        """Refresh all data displays."""
        self.refresh_expense_list()
        self.refresh_summary()
        self.refresh_categories()

    def refresh_expense_list(self):
        """Refresh the expense list table."""
        expenses = self.expense_controller.get_expenses()

        # Get the correct currency symbol from config
        currency_symbol = self.config["data"]["currency"]["symbol"]

        # Show only the 100 most recent expenses
        recent_expenses = expenses[:100]
        self.expense_table.setRowCount(len(recent_expenses))

        for row, expense in enumerate(recent_expenses):
            self.expense_table.setItem(row, 0, QTableWidgetItem(expense.date))
            self.expense_table.setItem(
                row, 1, QTableWidgetItem(expense.format_amount(currency_symbol))
            )
            self.expense_table.setItem(row, 2, QTableWidgetItem(expense.category))
            self.expense_table.setItem(row, 3, QTableWidgetItem(expense.description))

    def refresh_summary(self):
        """Refresh the summary dashboard."""
        summary = self.expense_controller.get_expense_summary()

        # Get the correct currency symbol from config
        currency_symbol = self.config["data"]["currency"]["symbol"]

        # Update the three separate cards
        self.income_label.setText(f"{currency_symbol}{summary['total_income']:.2f}")
        self.expenses_label.setText(f"{currency_symbol}{summary['total_expenses']:.2f}")

        # Format net balance with appropriate color
        net_balance = summary["net_balance"]
        if net_balance >= 0:
            self.balance_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #28a745;"  # Green for positive
            )
            self.balance_label.setText(f"{currency_symbol}{net_balance:.2f}")
        else:
            self.balance_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #dc3545;"  # Red for negative
            )
            self.balance_label.setText(f"-{currency_symbol}{abs(net_balance):.2f}")

        # Update status bar with insights if available
        if summary.get("insights"):
            insight = summary["insights"][0]  # Show first insight
            self.status_bar.showMessage(f"💡 {insight}")

    def refresh_categories(self):
        """Refresh the category dropdown."""
        # Get categories from expense data
        expenses = self.expense_controller.get_expenses()
        categories = list(set(expense.category for expense in expenses))

        # Add default categories from config if no expenses exist
        if not categories:
            categories = self.config["data"]["default_categories"]
        else:
            # Combine with default categories and remove duplicates
            all_categories = categories + self.config["data"]["default_categories"]
            categories = sorted(list(set(all_categories)))

        current_text = self.category_combo.currentText()

        self.category_combo.clear()
        self.category_combo.addItems(categories)

        # Restore current selection if it still exists
        if current_text in categories:
            self.category_combo.setCurrentText(current_text)

    def switch_data_source(self):
        """Switch between mock data and Google Sheets."""
        index = self.data_source_combo.currentIndex()

        if index == 0:  # Mock data
            self.use_mock_data = True
            self.expense_controller.switch_data_source(use_mock_data=True)
            self.connection_status.setText("Status: Mock data active")
            self.connection_status.setStyleSheet("color: #28a745; font-weight: bold;")
        else:  # Google Sheets
            self.use_mock_data = False
            self.expense_controller.switch_data_source(use_mock_data=False)
            self.connection_status.setText("Status: Google Sheets selected")
            self.connection_status.setStyleSheet("color: #007acc; font-weight: bold;")

        self.refresh_data()
        self.status_bar.showMessage(
            f"Switched to {'Mock Data' if self.use_mock_data else 'Google Sheets'}"
        )

    def test_connection(self):
        """Test connection to the current data service."""
        # Disable button and show loading state
        self.test_connection_btn.setEnabled(False)
        original_text = self.test_connection_btn.text()
        self.test_connection_btn.setText("Testing...")

        # Update status bar
        self.status_bar.showMessage("Testing connection to Google Sheets...")

        # Process events to update UI
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        try:
            status = self.expense_controller.get_data_service_status()
        finally:
            # Restore button state
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText(original_text)
        result = (
            status["details"]
            if "details" in status
            else {"success": status["connected"], "message": status["message"]}
        )

        if result["success"]:
            QMessageBox.information(
                self,
                "Connection Test",
                f"✅ {result['message']}\n\nDetails:\n"
                + f"Source: {result.get('spreadsheet_title', 'Local Data')}\n"
                + f"Worksheets: {', '.join(result.get('worksheets', []))}",
            )
            status_color = "#28a745"
        else:
            error_message = result["message"]

            if "Credentials file not found" in error_message:
                enhanced_message = (
                    "❌ Google Sheets Setup Required\n\n"
                    "Missing: Google API credentials file\n"
                    "Expected location: config/credentials.json\n\n"
                    "🚀 Quick Setup:\n"
                    "1. Visit: console.cloud.google.com\n"
                    "2. Create/select project\n"
                    "3. Enable Google Sheets API\n"
                    "4. Create OAuth credentials\n"
                    "5. Download as credentials.json\n\n"
                    "📚 Full guide: docs/google_sheets_setup.md"
                )
                QMessageBox.warning(
                    self, "Google Sheets Setup Required", enhanced_message
                )
            elif "Spreadsheet ID not configured" in error_message:
                QMessageBox.warning(
                    self,
                    "Configuration Required",
                    f"❌ {error_message}\n\n"
                    f"Please enter your Google Sheets ID above and click 'Save Spreadsheet ID'.",
                )
            else:
                QMessageBox.warning(self, "Connection Test", f"❌ {error_message}")

            status_color = "#dc3545"

        self.connection_status.setText(f"Status: {result['message']}")
        self.connection_status.setStyleSheet(
            f"color: {status_color}; font-weight: bold;"
        )

    def sync_data(self):
        """Perform data synchronization."""
        # Disable button and show loading state
        self.sync_now_btn.setEnabled(False)
        original_text = self.sync_now_btn.text()
        self.sync_now_btn.setText("Syncing...")

        # Update status bar
        self.status_bar.showMessage("Synchronizing with Google Sheets...")

        # Process events to update UI
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        try:
            result = self.expense_controller.sync_data()
        finally:
            # Restore button state
            self.sync_now_btn.setEnabled(True)
            self.sync_now_btn.setText(original_text)

        if result["success"]:
            QMessageBox.information(
                self,
                "Sync Complete",
                f"✅ {result['message']}\n\n"
                + f"Summary: {result.get('summary', {}).get('count', 0)} expenses loaded",
            )
            self.refresh_data()
        else:
            # Enhanced error messaging for Google Sheets setup
            error_message = result["message"]

            if "Credentials file not found" in error_message:
                enhanced_message = (
                    "❌ Google Sheets Setup Required\n\n"
                    "The app needs Google API credentials to connect to Google Sheets.\n\n"
                    "Quick Setup Guide:\n"
                    "1. Go to Google Cloud Console (console.cloud.google.com)\n"
                    "2. Create a new project or select existing one\n"
                    "3. Enable Google Sheets API\n"
                    "4. Create OAuth 2.0 credentials\n"
                    "5. Download as 'credentials.json' and place in config/ folder\n\n"
                    "📚 See docs/google_sheets_setup.md for detailed instructions\n\n"
                    "💡 Tip: You can continue using Mock Data mode while setting this up!"
                )
                QMessageBox.warning(
                    self, "Google Sheets Setup Required", enhanced_message
                )
            else:
                QMessageBox.warning(self, "Sync Failed", f"❌ {error_message}")

        self.status_bar.showMessage(result["message"])

    def save_spreadsheet_id(self):
        """Save the spreadsheet ID to configuration."""
        spreadsheet_id = self.spreadsheet_id_edit.text().strip()

        if not spreadsheet_id:
            QMessageBox.warning(self, "Invalid Input", "Please enter a spreadsheet ID.")
            return

        # Disable button and show loading state
        self.save_spreadsheet_id_btn.setEnabled(False)
        original_text = self.save_spreadsheet_id_btn.text()
        self.save_spreadsheet_id_btn.setText("Saving...")

        # Update status bar
        self.status_bar.showMessage("Saving spreadsheet configuration...")

        # Process events to update UI
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        try:
            self.config_manager.update_spreadsheet_id(spreadsheet_id)

            # Reload the config to reflect the changes
            self.config_manager.reload_config()
            self.config = self.config_manager.get_config()

            # Update the UI field to reflect the saved value
            self.spreadsheet_id_edit.setText(
                self.config.get("google_sheets", {}).get("spreadsheet_id", "")
            )

            # Refresh Google Sheets status
            self.refresh_google_sheets_status()

            # Show feedback
            self.show_success_feedback(
                f"✅ Spreadsheet ID saved: {spreadsheet_id[:20]}..."
            )
            QMessageBox.information(self, "Saved", "Spreadsheet ID saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save spreadsheet ID: {e}")
        finally:
            # Restore button state
            self.save_spreadsheet_id_btn.setEnabled(True)
            self.save_spreadsheet_id_btn.setText(original_text)

    def reset_sample_data(self):
        """Reset to sample data (mock service only)."""
        if not self.use_mock_data:
            QMessageBox.information(
                self, "Info", "This function only works with Mock Data mode."
            )
            return

        reply = QMessageBox.question(
            self,
            "Reset Sample Data",
            "This will replace all current data with sample expenses. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.expense_controller.mock_service.reset_to_sample_data()
            self.refresh_data()
            QMessageBox.information(
                self, "Reset Complete", "Sample data has been loaded!"
            )

    def clear_all_data(self):
        """Factory reset - clear all data and return app to fresh state."""
        if not self.use_mock_data:
            QMessageBox.information(
                self, "Info", "This function only works with Mock Data mode."
            )
            return

        # Offer to export data first
        backup_reply = QMessageBox.question(
            self,
            "Backup Recommended",
            "💾 BACKUP RECOMMENDED 💾\n\n"
            "Before performing a factory reset, would you like to:\n\n"
            "• Export your data to CSV first? (Recommended)\n\n"
            "This will save all your transactions to a file "
            "so you can import them later if needed.",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )

        if backup_reply == QMessageBox.Cancel:
            return
        elif backup_reply == QMessageBox.Yes:
            # Export data first
            try:
                success, result = self.expense_controller.export_data(format_type="csv")
                if success:
                    QMessageBox.information(
                        self,
                        "Backup Complete",
                        f"Data exported to:\n{result}\n\nNow proceeding with factory reset...",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Backup Failed",
                        f"Export failed: {result}\n\nFactory reset cancelled for safety.",
                    )
                    return
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Backup Error",
                    f"Export failed: {e}\n\nFactory reset cancelled for safety.",
                )
                return

        # Proceed with reset confirmation
        reply = QMessageBox.question(
            self,
            "Factory Reset",
            "⚠️ FACTORY RESET WARNING ⚠️\n\n"
            "This will permanently delete ALL data:\n"
            "• All expense and credit transactions\n"
            "• All recurring expenses\n"
            "• Email configuration\n"
            "• Custom settings (currency will reset to £)\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you absolutely sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Second confirmation for safety
            final_reply = QMessageBox.question(
                self,
                "Final Confirmation",
                "🚨 LAST CHANCE 🚨\n\n"
                "You are about to erase ALL DATA.\n"
                "This will reset the app to factory defaults.\n\n"
                "Type 'DELETE' to confirm:",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if final_reply == QMessageBox.Yes:
                self.perform_factory_reset()

    def perform_factory_reset(self):
        """Perform comprehensive factory reset of all application data."""
        try:
            import yaml
            from pathlib import Path

            # 1. Clear all expense/transaction data
            self.expense_controller.mock_service.clear_all_data()

            # 2. Reset configuration to defaults
            default_config = {
                "app": {
                    "name": "Spending Tracker GUI",
                    "version": "1.0.0",
                    "debug": False,
                    "window": {
                        "title": "Spending Tracker",
                        "width": 1200,
                        "height": 800,
                        "resizable": True,
                    },
                },
                "google_sheets": {
                    "spreadsheet_id": "",
                    "worksheets": {
                        "expenses": "Expenses",
                        "categories": "Categories",
                        "budgets": "Budgets",
                        "summary": "Summary",
                    },
                    "credentials_file": "config/credentials.json",
                    "token_file": "config/token.json",
                },
                "data": {
                    "default_categories": [
                        "Food & Dining",
                        "Transportation",
                        "Shopping",
                        "Entertainment",
                        "Bills & Utilities",
                        "Healthcare",
                        "Travel",
                        "Income",
                        "Salary",
                        "Gift",
                        "Refund",
                        "Other",
                    ],
                    "date_format": "%Y-%m-%d",
                    "currency": {"symbol": "£", "code": "GBP", "decimal_places": 2},
                    "available_currencies": [
                        {"symbol": "£", "code": "GBP", "name": "British Pound"},
                        {"symbol": "$", "code": "USD", "name": "US Dollar"},
                        {"symbol": "€", "code": "EUR", "name": "Euro"},
                        {"symbol": "¥", "code": "JPY", "name": "Japanese Yen"},
                        {"symbol": "C$", "code": "CAD", "name": "Canadian Dollar"},
                        {"symbol": "A$", "code": "AUD", "name": "Australian Dollar"},
                        {"symbol": "₹", "code": "INR", "name": "Indian Rupee"},
                        {"symbol": "¥", "code": "CNY", "name": "Chinese Yuan"},
                    ],
                    "recurring_expenses": [],
                },
                "ui": {
                    "theme": "light",
                    "colors": {
                        "primary": "#007acc",
                        "secondary": "#f5f5f5",
                        "success": "#28a745",
                        "warning": "#ffc107",
                        "danger": "#dc3545",
                    },
                    "charts": {"default_type": "pie", "animation": True},
                },
                "backup": {
                    "enabled": True,
                    "frequency": "daily",
                    "local_backup_dir": "backups/",
                    "max_backups": 30,
                },
                "email": {
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "use_tls": True,
                    "from_email": "",
                    "from_name": "Spending Tracker",
                    "recipients": [],
                    "schedule": {
                        "enabled": False,
                        "send_monthly": True,
                        "day_of_month": 1,
                        "hour": 9,
                        "minute": 0,
                        "subject_prefix": "[Monthly Report] ",
                        "include_csv_attachment": True,
                    },
                    "templates": {
                        "monthly_subject": "Monthly Spending Summary - {start_date} to {end_date}",
                        "include_category_breakdown": True,
                        "include_recent_expenses": True,
                        "recent_expenses_limit": 20,
                    },
                },
            }

            # Save the reset configuration
            with open(self.config_manager.config_path, "w", encoding="utf-8") as file:
                yaml.dump(
                    default_config, file, default_flow_style=False, sort_keys=False
                )

            # 3. Reload configuration and UI
            self.config_manager.reload_config()
            self.config = self.config_manager.get_config()

            # 4. Reset UI elements to defaults
            self.spreadsheet_id_edit.setText("")
            self.amount_spin.setPrefix("£")

            # 5. Refresh all data displays
            self.refresh_data()
            self.load_currencies()
            self.refresh_google_sheets_status()

            # 6. Show completion message
            QMessageBox.information(
                self,
                "Factory Reset Complete",
                "✅ Factory reset completed successfully!\n\n"
                "The application has been returned to its default state:\n"
                "• All transactions cleared\n"
                "• All recurring expenses removed\n"
                "• Settings reset to defaults\n"
                "• Currency reset to £ (GBP)\n"
                "• Email configuration cleared\n\n"
                "The app is now in a fresh, clean state.",
            )

            self.show_success_feedback(
                "✅ Factory reset completed - app returned to fresh state"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Factory Reset Failed",
                f"❌ Factory reset failed:\n{str(e)}\n\n"
                "The application may be in an inconsistent state. "
                "Please restart the application.",
            )

    def export_csv(self):
        """Export data to CSV file."""
        if not self.use_mock_data:
            QMessageBox.information(
                self, "Info", "CSV export currently only available for Mock Data mode."
            )
            return

        try:
            success, result = self.expense_controller.export_data(format_type="csv")
            if success:
                QMessageBox.information(
                    self, "Export Complete", f"Data exported to:\n{result}"
                )
                self.status_bar.showMessage(f"Data exported to {result}")
            else:
                QMessageBox.warning(self, "Export Failed", result)
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Export failed: {e}")

    def load_currencies(self):
        """Load available currencies into the combo box."""
        currencies = self.config.get("data", {}).get("available_currencies", [])
        current_currency = self.config.get("data", {}).get("currency", {})
        current_symbol = current_currency.get("symbol", "$")

        self.currency_combo.clear()
        current_index = 0

        for i, currency in enumerate(currencies):
            display_text = (
                f"{currency['symbol']} - {currency['name']} ({currency['code']})"
            )
            self.currency_combo.addItem(display_text)

            # Set current selection
            if currency["symbol"] == current_symbol:
                current_index = i

        self.currency_combo.setCurrentIndex(current_index)

    def on_currency_changed(self):
        """Handle currency selection change."""
        # Update the amount spin box prefix immediately
        selected_text = self.currency_combo.currentText()
        if selected_text:
            symbol = selected_text.split(" - ")[0]
            self.amount_spin.setPrefix(symbol)

    def save_currency(self):
        """Save the selected currency to configuration."""
        selected_text = self.currency_combo.currentText()
        if not selected_text:
            return

        try:
            # Parse selected currency
            symbol = selected_text.split(" - ")[0]
            code = selected_text.split("(")[-1].replace(")", "")

            # Update config
            config = self.config_manager.get_config()
            config["data"]["currency"]["symbol"] = symbol
            config["data"]["currency"]["code"] = code

            # Save to file
            import yaml

            with open(self.config_manager.config_path, "w", encoding="utf-8") as file:
                yaml.dump(config, file, default_flow_style=False, sort_keys=False)

            # Update the amount spin box
            self.amount_spin.setPrefix(symbol)

            # Show feedback
            self.show_success_feedback(f"✅ Currency changed to {symbol} ({code})")
            QMessageBox.information(
                self, "Currency Updated", f"Currency changed to {symbol} ({code})"
            )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save currency: {e}")

    def show_success_feedback(self, message):
        """Show visual success feedback to user."""
        # Update status bar with success styling
        self.status_bar.showMessage(message)

        # Change status bar color temporarily
        original_style = self.status_bar.styleSheet()
        self.status_bar.setStyleSheet(
            "background-color: #d4edda; color: #155724; font-weight: bold; padding: 4px;"
        )

        # Create a timer to reset the styling
        from PySide6.QtCore import QTimer

        timer = QTimer()
        timer.timeout.connect(lambda: self.reset_status_bar_style(original_style))
        timer.setSingleShot(True)
        timer.start(3000)  # Reset after 3 seconds

        # Store timer reference to prevent garbage collection
        self._status_timer = timer

    def reset_status_bar_style(self, original_style):
        """Reset status bar to original styling."""
        self.status_bar.setStyleSheet(original_style)
        self.status_bar.showMessage("Ready")

    def load_spreadsheet_id(self):
        """Load the saved spreadsheet ID from configuration into the UI field."""
        try:
            # Reload config to ensure we have the latest values
            self.config_manager.reload_config()
            self.config = self.config_manager.get_config()

            # Load the spreadsheet ID from config
            spreadsheet_id = self.config.get("google_sheets", {}).get(
                "spreadsheet_id", ""
            )
            self.spreadsheet_id_edit.setText(spreadsheet_id)

            # Update status if we have a spreadsheet ID
            if spreadsheet_id and hasattr(self, "status_bar"):
                self.status_bar.showMessage(
                    f"Loaded saved spreadsheet ID: {spreadsheet_id[:20]}..."
                )
        except Exception as e:
            print(f"Warning: Could not load spreadsheet ID: {e}")

    def load_saved_settings(self):
        """Load all saved settings after UI is fully created."""
        # Load spreadsheet ID
        self.load_spreadsheet_id()

        # Refresh Google Sheets status
        self.refresh_google_sheets_status()

    def refresh_google_sheets_status(self):
        """Refresh the status indicators for Google Sheets setup components."""
        from pathlib import Path

        # Check Spreadsheet ID
        spreadsheet_id = self.config.get("google_sheets", {}).get("spreadsheet_id", "")
        if spreadsheet_id and spreadsheet_id.strip():
            self.spreadsheet_status.setText("✅ Set")
            self.spreadsheet_status.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.spreadsheet_status.setText("❌ Not set")
            self.spreadsheet_status.setStyleSheet("color: #dc3545; font-weight: bold;")

        # Check credentials.json file
        project_root = Path(__file__).parent.parent.parent
        credentials_path = project_root / "config" / "credentials.json"
        if credentials_path.exists():
            self.credentials_status.setText("✅ Found")
            self.credentials_status.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.credentials_status.setText("❌ Missing")
            self.credentials_status.setStyleSheet("color: #dc3545; font-weight: bold;")

        # Check token.json file (created after first successful auth)
        token_path = project_root / "config" / "token.json"
        if token_path.exists():
            self.token_status.setText("✅ Found")
            self.token_status.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.token_status.setText("❌ Missing")
            self.token_status.setStyleSheet("color: #ffc107; font-weight: bold;")

        # Update status bar with overall setup status
        if hasattr(self, "status_bar"):
            if spreadsheet_id and credentials_path.exists():
                if token_path.exists():
                    self.status_bar.showMessage("✅ Google Sheets setup complete")
                else:
                    self.status_bar.showMessage(
                        "🔑 Google Sheets ready - auth required on first use"
                    )
            else:
                self.status_bar.showMessage("⚙️ Google Sheets setup incomplete")

    def open_setup_guide(self):
        """Open the Google Sheets setup guide in the default text editor."""
        import subprocess
        import os
        from pathlib import Path

        try:
            project_root = Path(__file__).parent.parent.parent
            setup_guide_path = project_root / "docs" / "google_sheets_setup.md"

            if setup_guide_path.exists():
                # Use the default system handler to open the file
                if os.name == "nt":  # Windows
                    os.startfile(str(setup_guide_path))
                else:  # macOS and Linux
                    subprocess.run(
                        [
                            "open" if sys.platform == "darwin" else "xdg-open",
                            str(setup_guide_path),
                        ]
                    )

                self.status_bar.showMessage("📚 Opened Google Sheets setup guide")
            else:
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Setup guide not found at:\n{setup_guide_path}\n\n"
                    "Please check that docs/google_sheets_setup.md exists in your project.",
                )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open setup guide: {e}")

    def check_and_process_recurring_credit(self):
        """Check if recurring credit should be processed automatically."""
        try:
            from datetime import datetime

            credit_config = self.config.get("data", {}).get("recurring_credit", {})

            if not credit_config.get("enabled", False):
                return  # Recurring credit is disabled

            current_date = datetime.now()
            target_day = credit_config.get("day_of_month", 22)
            last_processed = credit_config.get("last_processed")
            current_month_key = current_date.strftime("%Y-%m")

            # Check if we should process this month's credit
            should_process = (
                current_date.day >= target_day  # We've reached or passed the target day
                and last_processed
                != current_month_key  # Haven't processed this month yet
            )

            if should_process:
                amount = credit_config.get("amount", 100.0)
                description = credit_config.get("description", "Monthly allowance")
                category = credit_config.get("category", "Income")

                # Process automatically
                credit_amount = -abs(amount)  # Negative = credit/income
                target_date = current_date.replace(day=target_day).strftime("%Y-%m-%d")

                success, message = self.expense_controller.add_expense(
                    target_date, credit_amount, category, f"[Auto] {description}"
                )

                if success:
                    # Update last processed
                    config = self.config_manager.get_config()
                    config["data"]["recurring_credit"][
                        "last_processed"
                    ] = current_month_key

                    import yaml

                    with open(
                        self.config_manager.config_path, "w", encoding="utf-8"
                    ) as file:
                        yaml.dump(
                            config, file, default_flow_style=False, sort_keys=False
                        )

                    # Show notification
                    self.show_success_feedback(
                        f"✅ Auto-processed monthly credit: {self.config['data']['currency']['symbol']}{amount:.2f}"
                    )
                    self.refresh_data()

        except Exception as e:
            print(f"Error checking recurring credit: {e}")

    def save_recurring_expense(self, date, amount, category, description):
        """Save a recurring expense to the configuration."""
        try:
            from datetime import datetime

            # Parse the date to get the day of month
            expense_date = datetime.strptime(date, "%Y-%m-%d")
            day_of_month = expense_date.day

            # Get current config
            config = self.config_manager.get_config()

            # Initialize recurring expenses list if it doesn't exist
            if "recurring_expenses" not in config["data"]:
                config["data"]["recurring_expenses"] = []

            # Create recurring expense entry
            recurring_expense = {
                "amount": amount,
                "category": category,
                "description": description,
                "day_of_month": day_of_month,
                "created_date": datetime.now().isoformat(),
                "last_processed": datetime.now().strftime("%Y-%m"),
                "enabled": True,
            }

            # Add to recurring expenses list
            config["data"]["recurring_expenses"].append(recurring_expense)

            # Save to file
            import yaml

            with open(self.config_manager.config_path, "w", encoding="utf-8") as file:
                yaml.dump(config, file, default_flow_style=False, sort_keys=False)

            # Reload config
            self.config_manager.reload_config()
            self.config = self.config_manager.get_config()

            print(
                f"Saved recurring expense: {description} - {self.config['data']['currency']['symbol']}{amount:.2f} on day {day_of_month}"
            )

        except Exception as e:
            print(f"Error saving recurring expense: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save recurring expense: {e}")

    def check_and_process_recurring_expenses(self):
        """Check if any recurring expenses should be processed automatically."""
        try:
            from datetime import datetime

            recurring_expenses = self.config.get("data", {}).get(
                "recurring_expenses", []
            )
            current_date = datetime.now()
            current_month_key = current_date.strftime("%Y-%m")

            processed_count = 0

            for expense in recurring_expenses:
                if not expense.get("enabled", True):
                    continue  # Skip disabled expenses

                target_day = expense.get("day_of_month", 1)
                last_processed = expense.get("last_processed")

                # Check if we should process this month's expense
                should_process = (
                    current_date.day
                    >= target_day  # We've reached or passed the target day
                    and last_processed
                    != current_month_key  # Haven't processed this month yet
                )

                if should_process:
                    amount = expense.get("amount", 0.0)
                    category = expense.get("category", "Other")
                    description = (
                        f"[Auto] {expense.get('description', 'Recurring expense')}"
                    )

                    # Create the target date (same day this month)
                    try:
                        target_date = current_date.replace(day=target_day).strftime(
                            "%Y-%m-%d"
                        )
                    except ValueError:
                        # Handle cases where the day doesn't exist in current month (e.g., Feb 30)
                        # Use the last day of the month instead
                        import calendar

                        last_day = calendar.monthrange(
                            current_date.year, current_date.month
                        )[1]
                        target_day = min(target_day, last_day)
                        target_date = current_date.replace(day=target_day).strftime(
                            "%Y-%m-%d"
                        )

                    # Add the expense
                    success, message = self.expense_controller.add_expense(
                        target_date, amount, category, description
                    )

                    if success:
                        # Update last processed date for this expense
                        expense["last_processed"] = current_month_key
                        processed_count += 1

            # Save updated config if any expenses were processed
            if processed_count > 0:
                config = self.config_manager.get_config()
                import yaml

                with open(
                    self.config_manager.config_path, "w", encoding="utf-8"
                ) as file:
                    yaml.dump(config, file, default_flow_style=False, sort_keys=False)

                # Show notification
                self.show_success_feedback(
                    f"✅ Auto-processed {processed_count} recurring expense{'s' if processed_count != 1 else ''}"
                )
                self.refresh_data()

        except Exception as e:
            print(f"Error checking recurring expenses: {e}")

    def view_recurring_expenses(self):
        """Show a dialog with all recurring expenses."""
        recurring_expenses = self.config.get("data", {}).get("recurring_expenses", [])

        if not recurring_expenses:
            QMessageBox.information(
                self,
                "No Recurring Expenses",
                "You don't have any recurring expenses set up yet.\n\n"
                "To create recurring expenses, check 'Make this a recurring monthly expense' "
                "when adding an expense in the Add Expense tab.",
            )
            return

        # Create a dialog to show recurring expenses
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Recurring Expenses")
        dialog.setIcon(QMessageBox.Information)

        # Build the message
        message = f"📅 You have {len(recurring_expenses)} recurring expense{'s' if len(recurring_expenses) != 1 else ''}:\n\n"

        for i, expense in enumerate(recurring_expenses, 1):
            status = "✅ Enabled" if expense.get("enabled", True) else "❌ Disabled"
            symbol = self.config["data"]["currency"]["symbol"]
            amount = expense.get("amount", 0.0)
            category = expense.get("category", "Other")
            description = expense.get("description", "No description")
            day = expense.get("day_of_month", 1)
            last_processed = expense.get("last_processed", "Never")

            message += f"{i}. {description}\n"
            message += f"   Amount: {symbol}{amount:.2f}\n"
            message += f"   Category: {category}\n"
            message += f"   Day of Month: {day}\n"
            message += f"   Status: {status}\n"
            message += f"   Last Processed: {last_processed}\n\n"

        message += "💡 Tip: Recurring expenses are automatically processed when you open the app "
        message += "and the target day has passed."

        dialog.setText(message)
        dialog.addButton("OK", QMessageBox.AcceptRole)
        dialog.exec()

    def process_all_recurring_expenses(self):
        """Manually process all recurring expenses that are due."""
        recurring_expenses = self.config.get("data", {}).get("recurring_expenses", [])

        if not recurring_expenses:
            QMessageBox.information(
                self,
                "No Recurring Expenses",
                "You don't have any recurring expenses set up yet.",
            )
            return

        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Process Recurring Expenses",
            "This will process all recurring expenses that are due for this month. "
            "Expenses already processed this month will be skipped.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Process recurring expenses
            self.check_and_process_recurring_expenses()

            # Show completion message
            QMessageBox.information(
                self,
                "Processing Complete",
                "Recurring expenses processing completed!\n\n"
                "Check the expense list to see any new entries. "
                "Expenses are marked with '[Auto]' in the description.",
            )

    def show_expense_context_menu(self, position):
        """Show context menu for expense table."""
        item = self.expense_table.itemAt(position)
        if item is None:
            return

        # Create context menu
        menu = QMenu(self)

        edit_action = menu.addAction("📝 Edit Expense")
        delete_action = menu.addAction("🗑️ Delete Expense")
        menu.addSeparator()
        duplicate_action = menu.addAction("📋 Duplicate Expense")

        # Show menu and handle selection
        action = menu.exec(self.expense_table.mapToGlobal(position))

        if action == edit_action:
            self.edit_selected_expense()
        elif action == delete_action:
            self.delete_selected_expense()
        elif action == duplicate_action:
            self.duplicate_selected_expense()

    def edit_selected_expense(self):
        """Edit the currently selected expense."""
        current_row = self.expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select an expense to edit."
            )
            return

        # Get the expense data from the table
        expenses = self.expense_controller.get_expenses()
        if current_row >= len(expenses):
            QMessageBox.warning(self, "Error", "Selected expense not found.")
            return

        expense = expenses[current_row]

        # Show edit dialog using a simple input dialog
        from PySide6.QtWidgets import QInputDialog

        # For now, show a simple message - full edit dialog can be implemented later
        QMessageBox.information(
            self,
            "Edit Expense",
            "Expense editing feature is being enhanced.\n"
            "Please delete and re-add the expense for now.",
        )
        return

        # TODO: Implement full edit dialog in future version

    def delete_selected_expense(self):
        """Delete the currently selected expense."""
        current_row = self.expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select an expense to delete."
            )
            return

        # Get the expense data
        expenses = self.expense_controller.get_expenses()
        if current_row >= len(expenses):
            QMessageBox.warning(self, "Error", "Selected expense not found.")
            return

        expense = expenses[current_row]

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Expense",
            f"Are you sure you want to delete this expense?\n\n"
            f"Date: {expense.date}\n"
            f"Amount: {expense.format_amount()}\n"
            f"Category: {expense.category}\n"
            f"Description: {expense.description}\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            success, message = self.expense_controller.delete_expense(expense)

            if success:
                # Auto-sync to Google Sheets if not using mock data
                if not self.use_mock_data:
                    sync_result = self.expense_controller.sync_data()
                    if not sync_result["success"]:
                        # Show sync warning but don't fail the deletion
                        self.status_bar.showMessage(
                            f"⚠️ Transaction deleted but sync failed: "
                            f"{sync_result['message']}"
                        )

                success_msg = f"✅ {message}"
                if not self.use_mock_data:
                    success_msg += " and synced to Google Sheets"
                self.show_success_feedback(success_msg)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Delete Failed", f"❌ {message}")

    def duplicate_selected_expense(self):
        """Duplicate the currently selected expense."""
        current_row = self.expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select an expense to duplicate."
            )
            return

        # Get the expense data
        expenses = self.expense_controller.get_expenses()
        if current_row >= len(expenses):
            QMessageBox.warning(self, "Error", "Selected expense not found.")
            return

        expense = expenses[current_row]

        # Fill the add transaction form with the selected transaction data
        from datetime import datetime

        date_obj = datetime.strptime(expense.date, "%Y-%m-%d")
        self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))

        # Set amount and credit checkbox based on whether it's negative (credit) or positive (expense)
        if expense.amount < 0:
            self.amount_spin.setValue(-expense.amount)  # Make positive for display
            self.credit_checkbox.setChecked(True)
        else:
            self.amount_spin.setValue(expense.amount)
            self.credit_checkbox.setChecked(False)

        self.category_combo.setCurrentText(expense.category)
        self.description_edit.setText(expense.description)
        self.recurring_expense_checkbox.setChecked(
            False
        )  # Don't duplicate as recurring

        # Switch to Add Transaction tab
        self.tab_widget.setCurrentIndex(0)  # Add Transaction is the first tab

        # Show feedback
        transaction_type = "Credit" if expense.amount < 0 else "Expense"
        self.show_success_feedback(
            f"✅ {transaction_type} duplicated to Add Transaction form - review and save"
        )

    # Email-related methods
    def load_email_settings(self):
        """Load email settings from configuration."""
        email_config = self.config.get("email", {})

        # Load SMTP settings
        self.smtp_server_edit.setText(email_config.get("smtp_server", ""))
        self.smtp_port_spin.setValue(email_config.get("smtp_port", 587))
        self.email_username_edit.setText(email_config.get("username", ""))

        # Load password and trigger validation
        password = email_config.get("password", "")
        self.email_password_edit.setText(password)
        if password:  # Only validate if password exists
            self.validate_password(
                password.replace(" ", "")
            )  # Validate cleaned password

        self.from_name_edit.setText(email_config.get("from_name", "Spending Tracker"))
        self.use_tls_checkbox.setChecked(email_config.get("use_tls", True))

        # Load recipients
        recipients = email_config.get("recipients", [])
        self.recipients_list.clear()
        for recipient in recipients:
            self.recipients_list.addItem(recipient)

        # Load schedule settings
        schedule_config = email_config.get("schedule", {})
        self.enable_scheduling_checkbox.setChecked(
            schedule_config.get("enabled", False)
        )
        self.schedule_day_spin.setValue(schedule_config.get("day_of_month", 1))
        self.schedule_hour_spin.setValue(schedule_config.get("hour", 9))
        self.schedule_minute_spin.setValue(schedule_config.get("minute", 0))
        self.subject_prefix_edit.setText(
            schedule_config.get("subject_prefix", "[Monthly Report] ")
        )
        self.include_csv_checkbox.setChecked(
            schedule_config.get("include_csv_attachment", True)
        )

        # Update status
        self.update_email_status()

    def test_email_connection(self):
        """Test the email connection."""
        # Save settings first
        self.save_email_settings()

        # Test connection
        success, message = self.email_service.test_connection()

        if success:
            QMessageBox.information(self, "Email Test", f"✅ {message}")
        else:
            QMessageBox.warning(self, "Email Test Failed", f"❌ {message}")

        self.update_email_status()

    def save_email_settings(self):
        """Save email settings to configuration."""
        try:
            config = self.config_manager.get_config()
            if "email" not in config:
                config["email"] = {}

            # Save SMTP settings
            config["email"].update(
                {
                    "smtp_server": self.smtp_server_edit.text(),
                    "smtp_port": self.smtp_port_spin.value(),
                    "username": self.email_username_edit.text(),
                    "password": self.email_password_edit.text(),
                    "from_name": self.from_name_edit.text(),
                    "use_tls": self.use_tls_checkbox.isChecked(),
                }
            )

            # Set from_email if not explicitly set
            if not config["email"].get("from_email"):
                config["email"]["from_email"] = self.email_username_edit.text()

            # Save current recipients from GUI list
            recipients = []
            for i in range(self.recipients_list.count()):
                recipients.append(self.recipients_list.item(i).text())
            config["email"]["recipients"] = recipients

            # Save configuration
            self.config_manager.save_config(config)
            self.config = config

            # Update email service (reset to trigger lazy reload)
            self._email_service = None

            self.show_success_feedback("✅ Email settings saved successfully")

        except Exception as e:
            QMessageBox.warning(
                self, "Save Error", f"Failed to save email settings: {str(e)}"
            )

    def add_email_recipient(self):
        """Add a new email recipient."""
        email = self.new_recipient_edit.text().strip()

        if not email:
            return

        # Basic email validation
        if "@" not in email or "." not in email.split("@")[-1]:
            QMessageBox.warning(
                self, "Invalid Email", "Please enter a valid email address."
            )
            return

        # Check if already exists
        for i in range(self.recipients_list.count()):
            if self.recipients_list.item(i).text() == email:
                QMessageBox.information(
                    self,
                    "Duplicate Email",
                    "This email address is already in the list.",
                )
                return

        # Add to list
        self.recipients_list.addItem(email)
        self.new_recipient_edit.clear()

        # Save to config
        self.save_email_recipients()

    def remove_email_recipient(self):
        """Remove selected email recipient."""
        current_item = self.recipients_list.currentItem()
        if current_item:
            row = self.recipients_list.row(current_item)
            self.recipients_list.takeItem(row)
            self.save_email_recipients()

    def save_email_recipients(self):
        """Save email recipients to configuration."""
        recipients = []
        for i in range(self.recipients_list.count()):
            recipients.append(self.recipients_list.item(i).text())

        self.email_service.update_recipients(recipients)
        self.config = self.config_manager.get_config()  # Refresh config

    def save_email_schedule(self):
        """Save email schedule settings."""
        self.email_scheduler.update_schedule_config(
            enabled=self.enable_scheduling_checkbox.isChecked(),
            day_of_month=self.schedule_day_spin.value(),
            hour=self.schedule_hour_spin.value(),
            minute=self.schedule_minute_spin.value(),
            subject_prefix=self.subject_prefix_edit.text(),
            include_csv=self.include_csv_checkbox.isChecked(),
        )

        self.show_success_feedback("✅ Email schedule settings saved")
        self.update_email_status()

    def start_email_scheduler(self):
        """Start the email scheduler."""
        if self.email_scheduler.start_scheduler():
            self.show_success_feedback("✅ Email scheduler started")
        else:
            QMessageBox.warning(
                self,
                "Scheduler Error",
                "Failed to start email scheduler. Check your settings.",
            )

        self.update_email_status()

    def stop_email_scheduler(self):
        """Stop the email scheduler."""
        if self.email_scheduler.stop_scheduler():
            self.show_success_feedback("✅ Email scheduler stopped")

        self.update_email_status()

    def send_monthly_report(self):
        """Send the monthly report manually."""
        success, message = self.email_scheduler.send_monthly_report()

        if success:
            QMessageBox.information(self, "Email Sent", f"✅ {message}")
        else:
            QMessageBox.warning(self, "Email Failed", f"❌ {message}")

    def send_test_email(self):
        """Send a test email with current data."""
        from datetime import date

        # Get current month's expenses
        today = date.today()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        success, message = self.email_scheduler.send_custom_report(start_date, end_date)

        if success:
            QMessageBox.information(self, "Test Email Sent", f"✅ {message}")
        else:
            QMessageBox.warning(self, "Test Email Failed", f"❌ {message}")

    def send_custom_report(self):
        """Send a custom date range report."""
        start_date = self.custom_start_date.date().toString("yyyy-MM-dd")
        end_date = self.custom_end_date.date().toString("yyyy-MM-dd")

        success, message = self.email_scheduler.send_custom_report(start_date, end_date)

        if success:
            QMessageBox.information(self, "Custom Report Sent", f"✅ {message}")
        else:
            QMessageBox.warning(self, "Custom Report Failed", f"❌ {message}")

    def update_email_status(self):
        """Update the email status displays."""
        if self.email_scheduler.is_running():
            next_time = self.email_scheduler.get_next_scheduled_time()
            if next_time:
                self.schedule_status_label.setText(
                    f"Status: Scheduler running - Next report: {next_time}"
                )
                self.schedule_status_label.setStyleSheet(
                    "color: #28a745; font-weight: bold;"
                )
            else:
                self.schedule_status_label.setText("Status: Scheduler running")
                self.schedule_status_label.setStyleSheet(
                    "color: #28a745; font-weight: bold;"
                )
        else:
            self.schedule_status_label.setText("Status: Scheduler stopped")
            self.schedule_status_label.setStyleSheet(
                "color: #dc3545; font-weight: bold;"
            )

    def on_tab_changed(self, index):
        """Handle tab change events."""
        # Update email status when Email Reports tab is selected (assuming it's the last tab)
        if index == self.tab_widget.count() - 1:  # Email Reports is the last tab
            self.update_email_status()

    def start_email_scheduler_on_launch(self):
        """Start email scheduler automatically if enabled in configuration."""
        try:
            # Check if email scheduling is enabled
            email_config = self.config.get("email", {})
            schedule_config = email_config.get("schedule", {})

            if schedule_config.get("enabled", False):
                # Only start if we have basic email configuration
                smtp_server = email_config.get("smtp_server", "")
                username = email_config.get("username", "")
                password = email_config.get("password", "")
                recipients = email_config.get("recipients", [])

                if smtp_server and username and password and recipients:
                    # Start the scheduler
                    if self.email_scheduler.start_scheduler():
                        # Small delay to ensure scheduler thread has started
                        import time

                        time.sleep(0.2)

                        # Force update the email status after startup
                        from PySide6.QtCore import QTimer

                        QTimer.singleShot(1000, self.update_email_status)
                        QTimer.singleShot(
                            3000, self.update_email_status
                        )  # Again after 3 seconds

                        # Show success in status bar
                        next_time = self.email_scheduler.get_next_scheduled_time()
                        if next_time:
                            QTimer.singleShot(
                                500,
                                lambda: self.status_bar.showMessage(
                                    f"📧 Email scheduler started - Next report: {next_time}"
                                ),
                            )
        except Exception as e:
            print(f"Error starting email scheduler on launch: {e}")

    def on_password_text_changed(self, text):
        """Handle password text changes with validation and auto-formatting."""
        # Don't process if we're already updating to prevent recursion
        if hasattr(self, "_updating_password") and self._updating_password:
            return

        self._updating_password = True

        # Store cursor position
        cursor_pos = self.email_password_edit.cursorPosition()

        # Remove spaces automatically
        cleaned_text = text.replace(" ", "")

        # Only update if text changed (to avoid infinite loop)
        if cleaned_text != text:
            self.email_password_edit.setText(cleaned_text)
            # Restore cursor position, adjusting for removed spaces
            new_pos = min(
                cursor_pos - (len(text) - len(cleaned_text)), len(cleaned_text)
            )
            self.email_password_edit.setCursorPosition(max(0, new_pos))

        # Validate password format
        self.validate_password(cleaned_text)

        self._updating_password = False

    def validate_password(self, password):
        """Validate the password format and show status."""
        if not password:
            # Empty password
            self.password_status_label.setText("")
            self.password_status_label.setToolTip("")
            self.email_password_edit.setStyleSheet("")
            return

        # Check if it's alphanumeric (typical for app passwords)
        is_alphanumeric = password.isalnum()

        if len(password) == 16 and is_alphanumeric:
            # Valid app password format
            self.password_status_label.setText("✅")
            self.password_status_label.setToolTip(
                "Valid app password format (16 alphanumeric characters)"
            )
            self.password_status_label.setStyleSheet(
                "color: #28a745; font-weight: bold;"
            )
            self.email_password_edit.setStyleSheet("border: 2px solid #28a745;")
        elif len(password) == 16 and not is_alphanumeric:
            # 16 characters but contains special characters
            self.password_status_label.setText("⚠️")
            self.password_status_label.setToolTip(
                "16 characters but contains non-alphanumeric characters.\nApp passwords are typically alphanumeric only."
            )
            self.password_status_label.setStyleSheet(
                "color: #ffc107; font-weight: bold;"
            )
            self.email_password_edit.setStyleSheet("border: 2px solid #ffc107;")
        elif len(password) < 16:
            # Too short
            self.password_status_label.setText("❌")
            self.password_status_label.setToolTip(
                f"Too short: {len(password)}/16 characters. App passwords should be 16 characters."
            )
            self.password_status_label.setStyleSheet(
                "color: #dc3545; font-weight: bold;"
            )
            self.email_password_edit.setStyleSheet("border: 2px solid #dc3545;")
        else:
            # Too long
            self.password_status_label.setText("❌")
            self.password_status_label.setToolTip(
                f"Too long: {len(password)} characters. App passwords should be exactly 16 characters."
            )
            self.password_status_label.setStyleSheet(
                "color: #dc3545; font-weight: bold;"
            )
            self.email_password_edit.setStyleSheet("border: 2px solid #dc3545;")

    def toggle_password_visibility(self):
        """Toggle between showing and hiding the password."""
        if self.email_password_edit.echoMode() == QLineEdit.Password:
            # Show password
            self.email_password_edit.setEchoMode(QLineEdit.Normal)
            self.password_toggle_btn.setText("🙈")  # Eye with hand covering
            self.password_toggle_btn.setToolTip("Click to hide password")
        else:
            # Hide password
            self.email_password_edit.setEchoMode(QLineEdit.Password)
            self.password_toggle_btn.setText("👁")  # Eye open
            self.password_toggle_btn.setToolTip("Click to show password")

    @property
    def expense_controller(self):
        """Lazy-load the expense controller."""
        if self._expense_controller is None:
            from src.controllers.expense_controller import ExpenseController

            self._expense_controller = ExpenseController(
                self.config_manager, use_mock_data=self.use_mock_data
            )
        return self._expense_controller

    @property
    def email_service(self):
        """Lazy-load the email service."""
        if self._email_service is None:
            from src.services.email_service import EmailService

            self._email_service = EmailService(self.config_manager)
        return self._email_service

    @property
    def email_scheduler(self):
        """Lazy-load the email scheduler."""
        if self._email_scheduler is None:
            from src.services.email_scheduler import EmailScheduler

            self._email_scheduler = EmailScheduler(
                self.config_manager, self.expense_controller
            )
        return self._email_scheduler

    def _complete_initialization(self):
        """Complete the heavy initialization after UI is shown."""
        try:
            # Update status to show initialization is happening
            self.status_bar.showMessage("Loading data...")

            # Setup connections
            self.status_bar.showMessage("Setting up connections...")
            self.setup_connections()

            # Load initial data in background
            self.status_bar.showMessage("Loading expense data...")
            self.load_initial_data()

            # Start email scheduler if enabled
            self.status_bar.showMessage("Initializing email services...")
            self.start_email_scheduler_on_launch()

            # Connect tab change event
            self.tab_widget.currentChanged.connect(self.on_tab_changed)

            # Update status to ready
            self.status_bar.showMessage("Ready - Welcome to Spending Tracker!")

        except Exception as e:
            import traceback

            error_msg = f"Initialization error: {e}"
            self.status_bar.showMessage(error_msg)
            # Print full traceback for debugging
            if sys.stdout and sys.stdout.isatty():
                print(f"Initialization failed: {traceback.format_exc()}")

    def closeEvent(self, event):
        """Handle application close event."""
        # Show confirmation for normal closes
        reply = QMessageBox.question(
            self,
            "Close Application",
            "Close Spending Tracker?",  # Shorter message for faster reading
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,  # Default to Yes for faster closing
        )

        if reply == QMessageBox.Yes:
            self._cleanup_and_close()
            event.accept()
        else:
            event.ignore()

    def _cleanup_and_close(self):
        """Perform cleanup operations before closing."""
        # Stop initialization timer if still running
        if hasattr(self, "initialization_timer"):
            self.initialization_timer.stop()

        # Stop email scheduler if it's running (with timeout)
        try:
            if self._email_scheduler and self._email_scheduler.is_running():
                # Use a timer to prevent hanging on shutdown
                QTimer.singleShot(100, self._email_scheduler.stop_scheduler)
        except Exception:
            # Silently ignore cleanup errors during shutdown
            pass


def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Spending Tracker")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Personal Finance Tools")

    # Show splash screen for user feedback
    from src.gui.splash_screen import show_splash_screen

    splash = show_splash_screen()

    # Process events to show splash screen
    app.processEvents()

    try:
        # Create main window
        splash.show_message("Creating main window...")
        app.processEvents()

        window = SpendingTrackerMainWindow()

        splash.show_message("Finalising...")
        app.processEvents()

        # Show main window and close splash
        window.show()
        splash.close()

    except Exception as e:
        splash.close()
        raise e

    # Run the application
    return app.exec()


# ExpenseEditDialog moved to separate module for better organization
# Will be imported when needed to reduce startup time


if __name__ == "__main__":
    sys.exit(main())
