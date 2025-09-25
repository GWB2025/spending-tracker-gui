#!/usr/bin/env python3
"""
Expense Data Model for Spending Tracker

This module defines the Expense data model and related validation logic.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


@dataclass
class Expense:
    """
    Data model for a transaction entry (expense or credit).

    Attributes:
        date: Date of the transaction (YYYY-MM-DD format)
        amount: Amount - negative for expenses/debits, positive for credits/income
        category: Transaction category
        description: Optional description
        id: Unique identifier
        created_at: Timestamp when transaction was created
        updated_at: Timestamp when transaction was last updated
    """

    date: str
    amount: float
    category: str
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Post-initialization validation and setup."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

        self.validate()

    def validate(self) -> None:
        """
        Validate expense data.

        Raises:
            ValueError: If any field contains invalid data
        """
        # Validate amount (negative for expenses, positive for credits/income)
        if not isinstance(self.amount, (int, float)) or self.amount == 0:
            raise ValueError("Amount must be a non-zero number")

        # Validate date format
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

        # Validate category
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")

        # Clean up string fields
        self.category = self.category.strip()
        self.description = self.description.strip() if self.description else ""

    def update(self, **kwargs) -> None:
        """
        Update expense fields and update timestamp.

        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.updated_at = datetime.now().isoformat()
        self.validate()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert expense to dictionary format.

        Returns:
            Dictionary representation of the expense
        """
        return {
            "id": self.id,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Expense":
        """
        Create expense from dictionary data.

        Args:
            data: Dictionary containing expense data

        Returns:
            Expense instance
        """
        # Handle legacy data without id or timestamps
        expense_data = {
            "date": data.get("Date", data.get("date")),
            "amount": float(data.get("Amount", data.get("amount", 0))),
            "category": data.get("Category", data.get("category", "")),
            "description": data.get("Description", data.get("description", "")),
        }

        # Add optional fields if present
        if "id" in data:
            expense_data["id"] = data["id"]
        if "created_at" in data or "Created At" in data:
            expense_data["created_at"] = data.get("created_at", data.get("Created At"))
        if "updated_at" in data:
            expense_data["updated_at"] = data["updated_at"]

        return cls(**expense_data)

    def format_amount(self, currency_symbol: str = "$") -> str:
        """
        Format amount with currency symbol.

        Args:
            currency_symbol: Currency symbol to use

        Returns:
            Formatted amount string (negative amounts show with minus sign)
        """
        if self.amount < 0:
            return f"-{currency_symbol}{abs(self.amount):.2f}"
        else:
            return f"{currency_symbol}{self.amount:.2f}"

    def format_date(self, format_string: str = "%B %d, %Y") -> str:
        """
        Format date for display.

        Args:
            format_string: Date format string

        Returns:
            Formatted date string
        """
        try:
            date_obj = datetime.strptime(self.date, "%Y-%m-%d")
            return date_obj.strftime(format_string)
        except ValueError:
            return self.date

    def is_in_month(self, year: int, month: int) -> bool:
        """
        Check if expense is in specific month.

        Args:
            year: Year to check
            month: Month to check (1-12)

        Returns:
            True if expense is in the specified month
        """
        try:
            date_obj = datetime.strptime(self.date, "%Y-%m-%d")
            return date_obj.year == year and date_obj.month == month
        except ValueError:
            return False

    def is_in_date_range(self, start_date: str, end_date: str) -> bool:
        """
        Check if expense is within date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            True if expense is within the date range
        """
        try:
            expense_date = datetime.strptime(self.date, "%Y-%m-%d")
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            return start <= expense_date <= end
        except ValueError:
            return False

    def __str__(self) -> str:
        """String representation of expense."""
        return (
            f"{self.format_date('%Y-%m-%d')} - {self.category}: {self.format_amount()}"
        )

    def __repr__(self) -> str:
        """Developer representation of expense."""
        return (
            f"Expense(date='{self.date}', amount={self.amount}, "
            f"category='{self.category}', description='{self.description}')"
        )


class ExpenseFilter:
    """Helper class for filtering expenses based on various criteria."""

    @staticmethod
    def by_category(expenses: List[Expense], category: str) -> List[Expense]:
        """Filter expenses by category."""
        return [exp for exp in expenses if exp.category.lower() == category.lower()]

    @staticmethod
    def by_amount_range(
        expenses: List[Expense], min_amount: float, max_amount: float
    ) -> List[Expense]:
        """Filter expenses by amount range."""
        return [exp for exp in expenses if min_amount <= exp.amount <= max_amount]

    @staticmethod
    def by_date_range(
        expenses: List[Expense], start_date: str, end_date: str
    ) -> List[Expense]:
        """Filter expenses by date range."""
        return [exp for exp in expenses if exp.is_in_date_range(start_date, end_date)]

    @staticmethod
    def by_month(expenses: List[Expense], year: int, month: int) -> List[Expense]:
        """Filter expenses by specific month."""
        return [exp for exp in expenses if exp.is_in_month(year, month)]

    @staticmethod
    def by_description_contains(
        expenses: List[Expense], search_term: str
    ) -> List[Expense]:
        """Filter expenses where description contains search term."""
        search_lower = search_term.lower()
        return [exp for exp in expenses if search_lower in exp.description.lower()]


class ExpenseAggregator:
    """Helper class for aggregating expense data."""

    @staticmethod
    def total_amount(expenses: List[Expense]) -> float:
        """Calculate total amount of expenses."""
        return sum(exp.amount for exp in expenses)

    @staticmethod
    def by_category(expenses: List[Expense]) -> Dict[str, float]:
        """Aggregate expenses by category."""
        category_totals = {}
        for expense in expenses:
            if expense.category in category_totals:
                category_totals[expense.category] += expense.amount
            else:
                category_totals[expense.category] = expense.amount
        return category_totals

    @staticmethod
    def by_month(expenses: List[Expense]) -> Dict[str, float]:
        """Aggregate expenses by month (YYYY-MM format)."""
        monthly_totals = {}
        for expense in expenses:
            try:
                month_key = expense.date[:7]  # Get YYYY-MM part
                if month_key in monthly_totals:
                    monthly_totals[month_key] += expense.amount
                else:
                    monthly_totals[month_key] = expense.amount
            except (ValueError, IndexError):
                continue
        return monthly_totals

    @staticmethod
    def total_expenses_only(expenses: List[Expense]) -> float:
        """Calculate total of expenses only (negative amounts)."""
        return sum(exp.amount for exp in expenses if exp.amount < 0)

    @staticmethod
    def total_income_only(expenses: List[Expense]) -> float:
        """Calculate total of income/credits only (positive amounts)."""
        return sum(exp.amount for exp in expenses if exp.amount > 0)

    @staticmethod
    def total_spending_absolute(expenses: List[Expense]) -> float:
        """Calculate total spending as absolute value (for traditional spending analysis)."""
        return abs(ExpenseAggregator.total_expenses_only(expenses))

    @staticmethod
    def average_per_day(expenses: List[Expense]) -> float:
        """Calculate average spending per day (based on days with expenses)."""
        if not expenses:
            return 0.0

        unique_dates = set(exp.date for exp in expenses)
        total_amount = ExpenseAggregator.total_amount(expenses)

        return total_amount / len(unique_dates) if unique_dates else 0.0
