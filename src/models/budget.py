#!/usr/bin/env python3
"""
Budget Data Model for Spending Tracker

This module defines the Budget data model for tracking spending limits by category.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid

from .expense import Expense, ExpenseFilter


@dataclass
class Budget:
    """
    Data model for a budget entry.

    Attributes:
        category: Category this budget applies to
        monthly_limit: Monthly spending limit for this category
        start_date: When this budget becomes active (YYYY-MM-DD)
        end_date: When this budget expires (YYYY-MM-DD), None for indefinite
        id: Unique identifier
        created_at: Timestamp when budget was created
        updated_at: Timestamp when budget was last updated
        is_active: Whether this budget is currently active
    """

    category: str
    monthly_limit: float
    start_date: str
    end_date: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True

    def __post_init__(self):
        """Post-initialization validation and setup."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

        self.validate()

    def validate(self) -> None:
        """
        Validate budget data.

        Raises:
            ValueError: If any field contains invalid data
        """
        # Validate monthly limit
        if not isinstance(self.monthly_limit, (int, float)) or self.monthly_limit <= 0:
            raise ValueError("Monthly limit must be a positive number")

        # Validate category
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")

        # Validate start date format
        try:
            datetime.strptime(self.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format")

        # Validate end date format if provided
        if self.end_date:
            try:
                end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
                start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")

                if end_dt <= start_dt:
                    raise ValueError("End date must be after start date")
            except ValueError as e:
                if "time data" in str(e):
                    raise ValueError("End date must be in YYYY-MM-DD format")
                raise e

        # Clean up string fields
        self.category = self.category.strip()

    def update(self, **kwargs) -> None:
        """
        Update budget fields and update timestamp.

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
        Convert budget to dictionary format.

        Returns:
            Dictionary representation of the budget
        """
        return {
            "id": self.id,
            "category": self.category,
            "monthly_limit": self.monthly_limit,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Budget":
        """
        Create budget from dictionary data.

        Args:
            data: Dictionary containing budget data

        Returns:
            Budget instance
        """
        budget_data = {
            "category": data.get("Category", data.get("category", "")),
            "monthly_limit": float(
                data.get("Monthly Budget", data.get("monthly_limit", 0))
            ),
            "start_date": data.get("start_date", datetime.now().strftime("%Y-%m-%d")),
        }

        # Add optional fields if present
        optional_fields = ["end_date", "id", "created_at", "updated_at", "is_active"]
        for field_name in optional_fields:
            if field_name in data:
                budget_data[field_name] = data[field_name]

        return cls(**budget_data)

    def is_active_for_date(self, date_str: str) -> bool:
        """
        Check if budget is active for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            True if budget is active for the given date
        """
        if not self.is_active:
            return False

        try:
            check_date = datetime.strptime(date_str, "%Y-%m-%d")
            start_date = datetime.strptime(self.start_date, "%Y-%m-%d")

            # Check if date is after start date
            if check_date < start_date:
                return False

            # Check if date is before end date (if end date is set)
            if self.end_date:
                end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
                if check_date > end_date:
                    return False

            return True

        except ValueError:
            return False

    def get_spending_for_month(
        self, year: int, month: int, expenses: List[Expense]
    ) -> float:
        """
        Calculate total spending for this budget's category in a specific month.
        With new sign convention: expenses are negative, so we take absolute value for budget tracking.

        Args:
            year: Year to check
            month: Month to check (1-12)
            expenses: List of all expenses

        Returns:
            Total spending for the category in the specified month (always positive)
        """
        # Filter expenses by category and month
        category_expenses = ExpenseFilter.by_category(expenses, self.category)
        month_expenses = ExpenseFilter.by_month(category_expenses, year, month)

        # For budget tracking, we only count actual expenses (negative amounts)
        # and return their absolute value for comparison with budget limits
        return abs(sum(exp.amount for exp in month_expenses if exp.amount < 0))

    def get_remaining_budget(
        self, year: int, month: int, expenses: List[Expense]
    ) -> float:
        """
        Calculate remaining budget for a specific month.

        Args:
            year: Year to check
            month: Month to check (1-12)
            expenses: List of all expenses

        Returns:
            Remaining budget amount (can be negative if over budget)
        """
        spent = self.get_spending_for_month(year, month, expenses)
        return self.monthly_limit - spent

    def is_over_budget(self, year: int, month: int, expenses: List[Expense]) -> bool:
        """
        Check if spending exceeds budget for a specific month.

        Args:
            year: Year to check
            month: Month to check (1-12)
            expenses: List of all expenses

        Returns:
            True if over budget
        """
        return self.get_remaining_budget(year, month, expenses) < 0

    def get_budget_percentage_used(
        self, year: int, month: int, expenses: List[Expense]
    ) -> float:
        """
        Get percentage of budget used for a specific month.

        Args:
            year: Year to check
            month: Month to check (1-12)
            expenses: List of all expenses

        Returns:
            Percentage of budget used (can exceed 100%)
        """
        spent = self.get_spending_for_month(year, month, expenses)
        return (spent / self.monthly_limit) * 100 if self.monthly_limit > 0 else 0

    def format_monthly_limit(self, currency_symbol: str = "$") -> str:
        """
        Format monthly limit with currency symbol.

        Args:
            currency_symbol: Currency symbol to use

        Returns:
            Formatted amount string
        """
        return f"{currency_symbol}{self.monthly_limit:.2f}"

    def __str__(self) -> str:
        """String representation of budget."""
        status = "Active" if self.is_active else "Inactive"
        return f"{self.category}: {self.format_monthly_limit()} monthly ({status})"

    def __repr__(self) -> str:
        """Developer representation of budget."""
        return (
            f"Budget(category='{self.category}', monthly_limit={self.monthly_limit}, "
            f"start_date='{self.start_date}', is_active={self.is_active})"
        )


class BudgetManager:
    """Helper class for managing multiple budgets."""

    def __init__(self, budgets: List[Budget] = None):
        """
        Initialize budget manager.

        Args:
            budgets: Initial list of budgets
        """
        self.budgets = budgets or []

    def add_budget(self, budget: Budget) -> None:
        """Add a new budget."""
        self.budgets.append(budget)

    def remove_budget(self, budget_id: str) -> bool:
        """
        Remove a budget by ID.

        Args:
            budget_id: ID of budget to remove

        Returns:
            True if budget was found and removed
        """
        for i, budget in enumerate(self.budgets):
            if budget.id == budget_id:
                self.budgets.pop(i)
                return True
        return False

    def get_budget_by_category(
        self, category: str, date_str: str = None
    ) -> Optional[Budget]:
        """
        Get active budget for a specific category.

        Args:
            category: Category to find budget for
            date_str: Date to check (defaults to today)

        Returns:
            Active budget for category, or None if not found
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        for budget in self.budgets:
            if (
                budget.category.lower() == category.lower()
                and budget.is_active_for_date(date_str)
            ):
                return budget

        return None

    def get_active_budgets(self, date_str: str = None) -> List[Budget]:
        """
        Get all budgets active for a specific date.

        Args:
            date_str: Date to check (defaults to today)

        Returns:
            List of active budgets
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        return [
            budget for budget in self.budgets if budget.is_active_for_date(date_str)
        ]

    def get_budget_status_for_month(
        self, year: int, month: int, expenses: List[Expense]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get budget status for all categories for a specific month.

        Args:
            year: Year to check
            month: Month to check (1-12)
            expenses: List of all expenses

        Returns:
            Dictionary with budget status for each category
        """
        month_date = f"{year}-{month:02d}-01"
        active_budgets = self.get_active_budgets(month_date)

        status = {}

        for budget in active_budgets:
            spent = budget.get_spending_for_month(year, month, expenses)
            remaining = budget.get_remaining_budget(year, month, expenses)
            percentage = budget.get_budget_percentage_used(year, month, expenses)

            status[budget.category] = {
                "budget_limit": budget.monthly_limit,
                "spent": spent,
                "remaining": remaining,
                "percentage_used": percentage,
                "over_budget": budget.is_over_budget(year, month, expenses),
                "budget_id": budget.id,
            }

        return status

    def get_total_budget_limit(self, date_str: str = None) -> float:
        """
        Get total budget limit across all active budgets.

        Args:
            date_str: Date to check (defaults to today)

        Returns:
            Total budget limit
        """
        active_budgets = self.get_active_budgets(date_str)
        return sum(budget.monthly_limit for budget in active_budgets)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all budgets to list of dictionaries."""
        return [budget.to_dict() for budget in self.budgets]

    @classmethod
    def from_dict_list(cls, data_list: List[Dict[str, Any]]) -> "BudgetManager":
        """
        Create budget manager from list of dictionaries.

        Args:
            data_list: List of budget dictionaries

        Returns:
            BudgetManager instance
        """
        budgets = [Budget.from_dict(data) for data in data_list]
        return cls(budgets)
