#!/usr/bin/env python3
"""
Mock Data Service for Spending Tracker

This service provides a local mock implementation for testing without Google Sheets.
Useful for development and demonstration purposes.
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import random

from src.config.config_manager import ConfigManager


class MockDataService:
    """Mock service that simulates Google Sheets functionality with local storage."""

    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize the mock data service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.data_file = self.data_dir / "expenses.json"

        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)

        # Load or create initial data
        self._load_data()

    def _load_data(self):
        """Load expense data from local JSON file."""
        if self.data_file.exists():
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        else:
            # Create initial demo data
            self.data = {
                "expenses": self._generate_sample_expenses(),
                "categories": [
                    "Food & Dining",
                    "Transportation",
                    "Shopping",
                    "Entertainment",
                    "Bills & Utilities",
                    "Healthcare",
                    "Travel",
                    "Other",
                ],
                "last_updated": datetime.now().isoformat(),
            }
            self._save_data()

    def _save_data(self):
        """Save expense data to local JSON file."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def _generate_sample_expenses(self) -> List[Dict[str, Any]]:
        """Generate sample expense data for demonstration."""
        categories = [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Other",
        ]

        descriptions = {
            "Food & Dining": [
                "Restaurant lunch",
                "Grocery shopping",
                "Coffee shop",
                "Pizza delivery",
                "Fast food",
            ],
            "Transportation": [
                "Gas station",
                "Parking fee",
                "Bus fare",
                "Uber ride",
                "Car maintenance",
            ],
            "Shopping": [
                "Clothing store",
                "Electronics",
                "Books",
                "Home goods",
                "Online purchase",
            ],
            "Entertainment": [
                "Movie tickets",
                "Concert",
                "Streaming service",
                "Video games",
                "Sports event",
            ],
            "Bills & Utilities": [
                "Electric bill",
                "Internet",
                "Phone bill",
                "Water bill",
                "Insurance",
            ],
            "Healthcare": [
                "Pharmacy",
                "Doctor visit",
                "Dentist",
                "Health insurance",
                "Vitamins",
            ],
            "Travel": [
                "Hotel",
                "Flight",
                "Car rental",
                "Travel insurance",
                "Vacation expenses",
            ],
            "Other": ["Gift", "Donation", "Subscription", "Bank fees", "Miscellaneous"],
        }

        expenses = []

        # Generate expenses for the last 30 days
        for i in range(50):  # 50 sample expenses
            date = datetime.now() - timedelta(days=random.randint(0, 30))
            category = random.choice(categories)
            description = random.choice(descriptions[category])

            # Generate realistic amounts based on category
            if category == "Bills & Utilities":
                amount = round(random.uniform(50, 200), 2)
            elif category == "Food & Dining":
                amount = round(random.uniform(5, 80), 2)
            elif category == "Transportation":
                amount = round(random.uniform(3, 60), 2)
            elif category == "Shopping":
                amount = round(random.uniform(15, 150), 2)
            elif category == "Travel":
                amount = round(random.uniform(100, 500), 2)
            else:
                amount = round(random.uniform(10, 100), 2)

            expenses.append(
                {
                    "Date": date.strftime("%Y-%m-%d"),
                    "Amount": amount,
                    "Category": category,
                    "Description": description,
                    "Created At": date.isoformat(),
                }
            )

        # Sort by date (most recent first)
        expenses.sort(key=lambda x: x["Date"], reverse=True)

        return expenses

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the mock connection (always successful).

        Returns:
            Dictionary with connection status and details.
        """
        return {
            "success": True,
            "message": "Mock service connection successful (local data)",
            "spreadsheet_title": "Mock Spending Tracker Data",
            "worksheets": ["Expenses", "Categories", "Summary"],
            "data_file": str(self.data_file),
            "expense_count": len(self.data["expenses"]),
        }

    def setup_spreadsheet_structure(self) -> bool:
        """Mock setup - always returns True."""
        return True

    def add_expense(
        self, date: str, amount: float, category: str, description: str = ""
    ) -> bool:
        """
        Add a new expense to the mock data.

        Args:
            date: Expense date in YYYY-MM-DD format
            amount: Expense amount
            category: Expense category
            description: Optional description

        Returns:
            True if successful.
        """
        try:
            expense = {
                "Date": date,
                "Amount": float(amount),
                "Category": category,
                "Description": description,
                "Created At": datetime.now().isoformat(),
            }

            self.data["expenses"].insert(0, expense)  # Add to beginning

            # Add category if it's new
            if category not in self.data["categories"]:
                self.data["categories"].append(category)

            self._save_data()
            return True

        except Exception as e:
            print(f"Error adding expense to mock service: {e}")
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
        Update an existing expense in the mock data.

        Args:
            old_expense: The original expense data dictionary
            date: New expense date in YYYY-MM-DD format
            amount: New expense amount
            category: New expense category
            description: New optional description

        Returns:
            True if successful.
        """
        try:
            # Extract old expense values, handling both uppercase and lowercase keys
            old_date = old_expense.get("Date") or old_expense.get("date")
            old_amount = old_expense.get("Amount") or old_expense.get("amount")
            old_category = old_expense.get("Category") or old_expense.get("category")
            old_description = old_expense.get("Description") or old_expense.get(
                "description", ""
            )

            # Find the expense to update
            for i, expense in enumerate(self.data["expenses"]):
                if (
                    expense["Date"] == old_date
                    and expense["Amount"] == old_amount
                    and expense["Category"] == old_category
                    and expense["Description"] == old_description
                ):

                    # Update the expense
                    self.data["expenses"][i] = {
                        "Date": date,
                        "Amount": float(amount),
                        "Category": category,
                        "Description": description,
                        "Created At": expense.get(
                            "Created At", datetime.now().isoformat()
                        ),  # Keep original created time
                    }

                    # Add category if it's new
                    if category not in self.data["categories"]:
                        self.data["categories"].append(category)

                    self._save_data()
                    return True

            # If we get here, the expense wasn't found
            print(
                f"Expense not found for update. Looking for: Date={old_date}, Amount={old_amount}, Category={old_category}, Description={old_description}"
            )
            return False

        except Exception as e:
            print(f"Error updating expense in mock service: {e}")
            return False

    def delete_expense(self, expense: Dict[str, Any]) -> bool:
        """
        Delete an existing expense from the mock data.

        Args:
            expense: The expense data dictionary to delete

        Returns:
            True if successful.
        """
        try:
            # Extract expense values, handling both uppercase and lowercase keys
            exp_date = expense.get("Date") or expense.get("date")
            exp_amount = expense.get("Amount") or expense.get("amount")
            exp_category = expense.get("Category") or expense.get("category")
            exp_description = expense.get("Description") or expense.get(
                "description", ""
            )

            # Find and remove the expense
            for i, existing_expense in enumerate(self.data["expenses"]):
                if (
                    existing_expense["Date"] == exp_date
                    and existing_expense["Amount"] == exp_amount
                    and existing_expense["Category"] == exp_category
                    and existing_expense["Description"] == exp_description
                ):

                    # Remove the expense
                    del self.data["expenses"][i]
                    self._save_data()
                    return True

            # If we get here, the expense wasn't found
            print(
                f"Expense not found for deletion. Looking for: Date={exp_date}, Amount={exp_amount}, Category={exp_category}, Description={exp_description}"
            )
            return False

        except Exception as e:
            print(f"Error deleting expense from mock service: {e}")
            return False

    def get_expenses(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve expenses from mock data.

        Args:
            limit: Maximum number of expenses to retrieve

        Returns:
            List of expense dictionaries.
        """
        expenses = self.data["expenses"]
        if limit:
            return expenses[:limit]
        return expenses

    def get_categories(self) -> List[str]:
        """
        Get list of expense categories from mock data.

        Returns:
            List of category names.
        """
        return self.data["categories"].copy()

    def get_spending_summary(self) -> Dict[str, float]:
        """
        Calculate spending summary from mock data.

        Returns:
            Dictionary with spending totals and averages.
        """
        try:
            expenses = self.data["expenses"]

            if not expenses:
                return {
                    "total": 0.0,
                    "this_month": 0.0,
                    "daily_average": 0.0,
                    "count": 0,
                }

            # Calculate totals
            total = sum(float(expense["Amount"]) for expense in expenses)

            # This month's expenses
            current_month = datetime.now().strftime("%Y-%m")
            this_month = sum(
                float(expense["Amount"])
                for expense in expenses
                if expense["Date"].startswith(current_month)
            )

            # Daily average (based on days with expenses)
            expense_dates = set(expense["Date"] for expense in expenses)
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
        Mock sync operation.

        Returns:
            Dictionary with sync status and details.
        """
        summary = self.get_spending_summary()

        return {
            "success": True,
            "message": "Mock sync completed (local data)",
            "summary": summary,
            "last_sync": datetime.now().isoformat(),
            "data_location": str(self.data_file),
        }

    def export_to_csv(self, file_path: Path = None) -> str:
        """
        Export expenses to CSV file.

        Args:
            file_path: Path to save CSV file. If None, uses default location.

        Returns:
            Path to the exported CSV file.
        """
        if file_path is None:
            file_path = (
                self.data_dir
                / f"expenses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                if not self.data["expenses"]:
                    return str(file_path)

                fieldnames = ["Date", "Amount", "Category", "Description"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for expense in self.data["expenses"]:
                    writer.writerow(
                        {
                            "Date": expense["Date"],
                            "Amount": expense["Amount"],
                            "Category": expense["Category"],
                            "Description": expense["Description"],
                        }
                    )

            return str(file_path)

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return ""

    def get_category_breakdown(self) -> Dict[str, float]:
        """
        Get spending breakdown by category.

        Returns:
            Dictionary with category names and total spending.
        """
        breakdown = {}

        for expense in self.data["expenses"]:
            category = expense["Category"]
            amount = float(expense["Amount"])

            if category in breakdown:
                breakdown[category] += amount
            else:
                breakdown[category] = amount

        # Round values
        return {k: round(v, 2) for k, v in breakdown.items()}

    def clear_all_data(self):
        """Clear all expense data (for testing purposes)."""
        self.data = {
            "expenses": [],
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Other",
            ],
            "last_updated": datetime.now().isoformat(),
        }
        self._save_data()

    def reset_to_sample_data(self):
        """Reset data to sample expenses (for demo purposes)."""
        self.data = {
            "expenses": self._generate_sample_expenses(),
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Other",
            ],
            "last_updated": datetime.now().isoformat(),
        }
        self._save_data()
