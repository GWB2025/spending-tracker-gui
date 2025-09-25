#!/usr/bin/env python3
"""
Google Sheets Service for Spending Tracker

This module handles all Google Sheets API interactions for expense data storage.
"""

from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config.config_manager import ConfigManager


class GoogleSheetsService:
    """Service for interacting with Google Sheets API."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize the Google Sheets service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_google_sheets_config()
        self.project_root = Path(__file__).parent.parent.parent

        self._service = None
        self._gspread_client = None
        self._spreadsheet = None

    def _get_credentials(self) -> Credentials:
        """Get valid credentials for Google Sheets API."""
        creds = None

        # Token file path
        token_path = self.project_root / self.config.get(
            "token_file", "config/token.json"
        )

        # Load existing token if it exists
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)

        # If there are no valid credentials, get them
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Load credentials file
                credentials_path = self.project_root / self.config.get(
                    "credentials_file", "config/credentials.json"
                )

                if not credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {credentials_path}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return creds

    def _get_service(self):
        """Get Google Sheets API service instance."""
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def _get_gspread_client(self):
        """Get gspread client instance."""
        if self._gspread_client is None:
            creds = self._get_credentials()
            self._gspread_client = gspread.authorize(creds)
        return self._gspread_client

    def _get_spreadsheet(self):
        """Get the spreadsheet instance."""
        if self._spreadsheet is None:
            spreadsheet_id = self.config.get("spreadsheet_id")
            if not spreadsheet_id:
                raise ValueError(
                    "Spreadsheet ID not configured. Please set it in config/config.yaml"
                )

            client = self._get_gspread_client()
            self._spreadsheet = client.open_by_key(spreadsheet_id)

        return self._spreadsheet

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Google Sheets.

        Returns:
            Dictionary with connection status and details.
        """
        try:
            spreadsheet = self._get_spreadsheet()

            return {
                "success": True,
                "message": "Connection successful",
                "spreadsheet_title": spreadsheet.title,
                "worksheets": [ws.title for ws in spreadsheet.worksheets()],
            }

        except FileNotFoundError as e:
            return {"success": False, "message": f"Credentials file not found: {e}"}
        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}

    def setup_spreadsheet_structure(self) -> bool:
        """
        Set up the required worksheet structure in the spreadsheet.

        Returns:
            True if setup successful, False otherwise.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            worksheets_config = self.config.get("worksheets", {})

            # Required worksheets
            required_sheets = {
                "expenses": worksheets_config.get("expenses", "Expenses"),
                "categories": worksheets_config.get("categories", "Categories"),
                "budgets": worksheets_config.get("budgets", "Budgets"),
                "summary": worksheets_config.get("summary", "Summary"),
            }

            existing_sheets = {ws.title for ws in spreadsheet.worksheets()}

            # Create missing worksheets
            for sheet_key, sheet_name in required_sheets.items():
                if sheet_name not in existing_sheets:
                    worksheet = spreadsheet.add_worksheet(
                        title=sheet_name, rows=1000, cols=10
                    )

                    # Set up headers based on sheet type
                    if sheet_key == "expenses":
                        headers = [
                            "Date",
                            "Amount",
                            "Category",
                            "Description",
                            "Created At",
                        ]
                        worksheet.append_row(headers)
                    elif sheet_key == "categories":
                        headers = ["Category", "Budget", "Color", "Created At"]
                        worksheet.append_row(headers)
                    elif sheet_key == "budgets":
                        headers = [
                            "Category",
                            "Monthly Budget",
                            "Current Spent",
                            "Remaining",
                            "Month",
                        ]
                        worksheet.append_row(headers)
                    elif sheet_key == "summary":
                        headers = ["Metric", "Value", "Period", "Updated At"]
                        worksheet.append_row(headers)

            return True

        except Exception as e:
            print(f"Error setting up spreadsheet structure: {e}")
            return False

    def add_expense(
        self, date: str, amount: float, category: str, description: str = ""
    ) -> bool:
        """
        Add a new expense to the spreadsheet.

        Args:
            date: Expense date in YYYY-MM-DD format
            amount: Expense amount
            category: Expense category
            description: Optional description

        Returns:
            True if successful, False otherwise.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            expenses_sheet_name = self.config.get("worksheets", {}).get(
                "expenses", "Expenses"
            )
            worksheet = spreadsheet.worksheet(expenses_sheet_name)

            # Prepare row data
            created_at = datetime.now().isoformat()
            row_data = [date, amount, category, description, created_at]

            # Append the row
            worksheet.append_row(row_data)

            return True

        except Exception as e:
            print(f"Error adding expense: {e}")
            return False

    def get_expenses(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve expenses from the spreadsheet.

        Args:
            limit: Maximum number of expenses to retrieve

        Returns:
            List of expense dictionaries.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            expenses_sheet_name = self.config.get("worksheets", {}).get(
                "expenses", "Expenses"
            )
            worksheet = spreadsheet.worksheet(expenses_sheet_name)

            # Get all records
            records = worksheet.get_all_records()

            if limit:
                records = records[-limit:]  # Get most recent

            return records

        except Exception as e:
            print(f"Error retrieving expenses: {e}")
            return []

    def get_categories(self) -> List[str]:
        """
        Get list of expense categories from the spreadsheet.

        Returns:
            List of category names.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            expenses_sheet_name = self.config.get("worksheets", {}).get(
                "expenses", "Expenses"
            )
            worksheet = spreadsheet.worksheet(expenses_sheet_name)

            # Get all category values (column C)
            categories = worksheet.col_values(3)[1:]  # Skip header

            # Return unique categories
            return list(set(filter(None, categories)))

        except Exception as e:
            print(f"Error retrieving categories: {e}")
            return []

    def get_spending_summary(self) -> Dict[str, float]:
        """
        Calculate spending summary from the spreadsheet data.

        Returns:
            Dictionary with spending totals and averages.
        """
        try:
            expenses = self.get_expenses()

            if not expenses:
                return {
                    "total": 0.0,
                    "this_month": 0.0,
                    "daily_average": 0.0,
                    "count": 0,
                }

            # Calculate totals
            total = sum(float(expense.get("Amount", 0)) for expense in expenses)

            # This month's expenses
            current_month = datetime.now().strftime("%Y-%m")
            this_month = sum(
                float(expense.get("Amount", 0))
                for expense in expenses
                if expense.get("Date", "").startswith(current_month)
            )

            # Daily average (based on days with expenses)
            expense_dates = set(
                expense.get("Date", "") for expense in expenses if expense.get("Date")
            )
            daily_average = total / len(expense_dates) if expense_dates else 0.0

            return {
                "total": round(total, 2),
                "this_month": round(this_month, 2),
                "daily_average": round(daily_average, 2),
                "count": len(expenses),
            }

        except Exception as e:
            print(f"Error calculating spending summary: {e}")
            return {"total": 0.0, "this_month": 0.0, "daily_average": 0.0, "count": 0}

    def sync_data(self) -> Dict[str, Any]:
        """
        Perform a full data synchronization.

        Returns:
            Dictionary with sync status and details.
        """
        try:
            # Test connection first
            connection_result = self.test_connection()
            if not connection_result["success"]:
                return connection_result

            # Setup spreadsheet structure if needed
            if not self.setup_spreadsheet_structure():
                return {
                    "success": False,
                    "message": "Failed to set up spreadsheet structure",
                }

            # Get summary data
            summary = self.get_spending_summary()

            return {
                "success": True,
                "message": "Sync completed successfully",
                "summary": summary,
                "last_sync": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"success": False, "message": f"Sync failed: {str(e)}"}
