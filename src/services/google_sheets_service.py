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
    
    def update_expense(
        self,
        old_expense: Dict[str, Any],
        date: str,
        amount: float,
        category: str,
        description: str = "",
    ) -> bool:
        """
        Update an existing expense in the spreadsheet.
        
        Args:
            old_expense: The original expense data dictionary
            date: New expense date in YYYY-MM-DD format
            amount: New expense amount
            category: New expense category
            description: New optional description
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            expenses_sheet_name = self.config.get("worksheets", {}).get(
                "expenses", "Expenses"
            )
            worksheet = spreadsheet.worksheet(expenses_sheet_name)
            
            # Extract old expense values, handling both uppercase and lowercase keys
            old_date = old_expense.get("Date") or old_expense.get("date")
            old_amount = old_expense.get("Amount") or old_expense.get("amount")
            old_category = old_expense.get("Category") or old_expense.get("category")
            old_description = old_expense.get("Description") or old_expense.get(
                "description", ""
            )
            
            # Get all records to find the matching row
            all_records = worksheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if (
                    record.get("Date") == old_date
                    and float(record.get("Amount", 0)) == float(old_amount)
                    and record.get("Category") == old_category
                    and record.get("Description") == old_description
                ):
                    # Found the matching record, update it (row index + 2 because of header and 1-based indexing)
                    row_num = i + 2
                    created_at = record.get("Created At", datetime.now().isoformat())
                    
                    # Update the row with new values
                    updated_row = [date, amount, category, description, created_at]
                    worksheet.update(f"A{row_num}:E{row_num}", [updated_row])
                    
                    return True
            
            # If we get here, the expense wasn't found
            print(
                f"Expense not found for update. Looking for: Date={old_date}, Amount={old_amount}, Category={old_category}, Description={old_description}"
            )
            return False
            
        except Exception as e:
            print(f"Error updating expense: {e}")
            return False
    
    def delete_expense(self, expense: Dict[str, Any]) -> bool:
        """
        Delete an existing expense from the spreadsheet.
        
        Args:
            expense: The expense data dictionary to delete
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            expenses_sheet_name = self.config.get("worksheets", {}).get(
                "expenses", "Expenses"
            )
            worksheet = spreadsheet.worksheet(expenses_sheet_name)
            
            # Extract expense values, handling both uppercase and lowercase keys
            exp_date = expense.get("Date") or expense.get("date")
            exp_amount = expense.get("Amount") or expense.get("amount")
            exp_category = expense.get("Category") or expense.get("category")
            exp_description = expense.get("Description") or expense.get(
                "description", ""
            )
            
            # Get all records to find the matching row
            all_records = worksheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if (
                    record.get("Date") == exp_date
                    and float(record.get("Amount", 0)) == float(exp_amount)
                    and record.get("Category") == exp_category
                    and record.get("Description") == exp_description
                ):
                    # Found the matching record, delete it (row index + 2 because of header and 1-based indexing)
                    row_num = i + 2
                    worksheet.delete_rows(row_num)
                    
                    return True
            
            # If we get here, the expense wasn't found
            print(
                f"Expense not found for deletion. Looking for: Date={exp_date}, Amount={exp_amount}, Category={exp_category}, Description={exp_description}"
            )
            return False
            
        except Exception as e:
            print(f"Error deleting expense: {e}")
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

    def sync_categories(self) -> bool:
        """
        Synchronize categories to the Categories sheet.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            categories_sheet_name = self.config.get("worksheets", {}).get(
                "categories", "Categories"
            )
            worksheet = spreadsheet.worksheet(categories_sheet_name)
            
            # Get unique categories from expenses
            categories = self.get_categories()
            
            # Clear existing data (except headers)
            worksheet.clear()
            
            # Set headers
            headers = ["Category", "Budget", "Color", "Created At"]
            worksheet.append_row(headers)
            
            # Add categories with default values
            for category in categories:
                row_data = [
                    category,
                    0.0,  # Default budget
                    "",   # Default color (empty)
                    datetime.now().isoformat()
                ]
                worksheet.append_row(row_data)
            
            return True
            
        except Exception as e:
            print(f"Error syncing categories: {e}")
            return False
    
    def sync_budgets(self) -> bool:
        """
        Synchronize budget data to the Budgets sheet.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            budgets_sheet_name = self.config.get("worksheets", {}).get(
                "budgets", "Budgets"
            )
            worksheet = spreadsheet.worksheet(budgets_sheet_name)
            
            # Get expenses to calculate current spending by category
            expenses = self.get_expenses()
            current_month = datetime.now().strftime("%Y-%m")
            
            # Calculate spending by category for current month
            category_spending = {}
            for expense in expenses:
                if expense.get("Date", "").startswith(current_month):
                    category = expense.get("Category", "")
                    amount = float(expense.get("Amount", 0))
                    if category:
                        category_spending[category] = category_spending.get(category, 0) + amount
            
            # Clear existing data (except headers)
            worksheet.clear()
            
            # Set headers
            headers = ["Category", "Monthly Budget", "Current Spent", "Remaining", "Month"]
            worksheet.append_row(headers)
            
            # Add budget data for each category with spending
            for category, spent in category_spending.items():
                budget = 0.0  # Default budget - could be enhanced to read from config
                remaining = budget - spent
                
                row_data = [
                    category,
                    budget,
                    round(spent, 2),
                    round(remaining, 2),
                    current_month
                ]
                worksheet.append_row(row_data)
            
            return True
            
        except Exception as e:
            print(f"Error syncing budgets: {e}")
            return False
    
    def sync_summary(self) -> bool:
        """
        Synchronize summary data to the Summary sheet.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            spreadsheet = self._get_spreadsheet()
            summary_sheet_name = self.config.get("worksheets", {}).get(
                "summary", "Summary"
            )
            worksheet = spreadsheet.worksheet(summary_sheet_name)
            
            # Get summary data
            summary = self.get_spending_summary()
            
            # Clear existing data (except headers)
            worksheet.clear()
            
            # Set headers
            headers = ["Metric", "Value", "Period", "Updated At"]
            worksheet.append_row(headers)
            
            # Add summary metrics
            current_time = datetime.now().isoformat()
            current_month = datetime.now().strftime("%Y-%m")
            
            summary_rows = [
                ["Total Expenses", summary.get("total", 0), "All Time", current_time],
                ["This Month", summary.get("this_month", 0), current_month, current_time],
                ["Daily Average", summary.get("daily_average", 0), "All Time", current_time],
                ["Transaction Count", summary.get("count", 0), "All Time", current_time]
            ]
            
            for row in summary_rows:
                worksheet.append_row(row)
            
            return True
            
        except Exception as e:
            print(f"Error syncing summary: {e}")
            return False

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
            
            # Sync all sheet data
            categories_synced = self.sync_categories()
            budgets_synced = self.sync_budgets()
            summary_synced = self.sync_summary()
            
            # Get summary data for response
            summary = self.get_spending_summary()
            
            sync_status = {
                "categories": categories_synced,
                "budgets": budgets_synced,
                "summary": summary_synced
            }

            return {
                "success": True,
                "message": "Sync completed successfully",
                "summary": summary,
                "sync_status": sync_status,
                "last_sync": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"success": False, "message": f"Sync failed: {str(e)}"}
