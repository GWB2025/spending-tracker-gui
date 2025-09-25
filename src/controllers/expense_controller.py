#!/usr/bin/env python3
"""
Expense Controller for Spending Tracker

This module provides business logic for expense management operations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.models.expense import Expense, ExpenseFilter, ExpenseAggregator
from src.models.budget import BudgetManager
from src.services.google_sheets_service import GoogleSheetsService
from src.services.mock_data_service import MockDataService
from src.config.config_manager import ConfigManager


class ExpenseController:
    """
    Controller for managing expense operations and business logic.

    This class serves as the main interface between the GUI and data services,
    providing higher-level operations and business rules.
    """

    def __init__(
        self, config_manager: ConfigManager = None, use_mock_data: bool = False
    ):
        """
        Initialize the expense controller.

        Args:
            config_manager: Configuration manager instance
            use_mock_data: Whether to use mock data service initially
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config()

        # Initialize data services
        self.mock_service = MockDataService(self.config_manager)
        self.sheets_service = GoogleSheetsService(self.config_manager)

        # Set initial data service
        self.use_mock_data = use_mock_data
        self.data_service = self.mock_service if use_mock_data else self.sheets_service

        # Initialize budget manager
        self.budget_manager = BudgetManager()

        # Cache for expenses to improve performance
        self._expense_cache: List[Expense] = []
        self._cache_last_updated: Optional[datetime] = None
        self._cache_duration_minutes = 5  # Cache expires after 5 minutes

    def switch_data_source(self, use_mock_data: bool) -> bool:
        """
        Switch between mock data and Google Sheets.

        Args:
            use_mock_data: True for mock data, False for Google Sheets

        Returns:
            True if switch was successful
        """
        try:
            self.use_mock_data = use_mock_data
            self.data_service = (
                self.mock_service if use_mock_data else self.sheets_service
            )
            self._invalidate_cache()
            return True
        except Exception as e:
            print(f"Error switching data source: {e}")
            return False

    def _invalidate_cache(self):
        """Invalidate the expense cache."""
        self._expense_cache = []
        self._cache_last_updated = None

    def _is_cache_valid(self) -> bool:
        """Check if the expense cache is still valid."""
        if not self._cache_last_updated:
            return False

        cache_age = datetime.now() - self._cache_last_updated
        return cache_age.total_seconds() < (self._cache_duration_minutes * 60)

    def _get_expenses_from_service(self) -> List[Expense]:
        """Get expenses from the current data service."""
        try:
            expense_data = self.data_service.get_expenses()
            return [Expense.from_dict(data) for data in expense_data]
        except Exception as e:
            print(f"Error loading expenses: {e}")
            return []

    def get_expenses(self, use_cache: bool = True) -> List[Expense]:
        """
        Get all expenses, optionally using cache for better performance.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            List of Expense objects
        """
        if use_cache and self._is_cache_valid():
            return self._expense_cache.copy()

        # Load fresh data
        self._expense_cache = self._get_expenses_from_service()
        self._cache_last_updated = datetime.now()

        return self._expense_cache.copy()

    def add_expense(
        self, date: str, amount: float, category: str, description: str = ""
    ) -> Tuple[bool, str]:
        """
        Add a new expense with validation and business rules.

        Args:
            date: Expense date in YYYY-MM-DD format
            amount: Expense amount
            category: Expense category
            description: Optional description

        Returns:
            Tuple of (success, message)
        """
        try:
            # Create and validate expense object
            expense = Expense(
                date=date, amount=amount, category=category, description=description
            )

            # Check if this expense would exceed any budget
            warnings = self._check_budget_warnings(expense)

            # Add to data service
            success = self.data_service.add_expense(date, amount, category, description)

            if success:
                self._invalidate_cache()  # Refresh cache on next access
                message = "Expense added successfully"
                if warnings:
                    message += f". {warnings}"
                return True, message
            else:
                return False, "Failed to add expense to data service"

        except ValueError as e:
            return False, f"Validation error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def update_expense(
        self,
        old_expense: Expense,
        date: str,
        amount: float,
        category: str,
        description: str = "",
    ) -> Tuple[bool, str]:
        """
        Update an existing expense with validation and business rules.

        Args:
            old_expense: The existing expense to update
            date: New expense date in YYYY-MM-DD format
            amount: New expense amount
            category: New expense category
            description: New optional description

        Returns:
            Tuple of (success, message)
        """
        try:
            # Create and validate new expense object
            new_expense = Expense(
                date=date, amount=amount, category=category, description=description
            )

            # Check if this expense would exceed any budget
            warnings = self._check_budget_warnings(new_expense)

            # Update in data service
            success = self.data_service.update_expense(
                old_expense.to_dict(), date, amount, category, description
            )

            if success:
                self._invalidate_cache()  # Refresh cache on next access
                message = "Expense updated successfully"
                if warnings:
                    message += f". {warnings}"
                return True, message
            else:
                return False, "Failed to update expense in data service"

        except ValueError as e:
            return False, f"Validation error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def delete_expense(self, expense: Expense) -> Tuple[bool, str]:
        """
        Delete an existing expense.

        Args:
            expense: The expense to delete

        Returns:
            Tuple of (success, message)
        """
        try:
            # Delete from data service
            success = self.data_service.delete_expense(expense.to_dict())

            if success:
                self._invalidate_cache()  # Refresh cache on next access
                return True, "Expense deleted successfully"
            else:
                return False, "Failed to delete expense from data service"

        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _check_budget_warnings(self, expense: Expense) -> str:
        """
        Check if expense would trigger budget warnings.

        Args:
            expense: The expense to check

        Returns:
            Warning message if applicable, empty string otherwise
        """
        try:
            expense_date = datetime.strptime(expense.date, "%Y-%m-%d")
            year, month = expense_date.year, expense_date.month

            budget = self.budget_manager.get_budget_by_category(
                expense.category, expense.date
            )

            if budget:
                current_expenses = self.get_expenses()
                projected_spending = (
                    budget.get_spending_for_month(year, month, current_expenses)
                    + expense.amount
                )

                if projected_spending > budget.monthly_limit:
                    overage = projected_spending - budget.monthly_limit
                    return f"⚠️ This will exceed your {expense.category} budget by ${overage:.2f}"
                elif projected_spending > (budget.monthly_limit * 0.8):  # 80% threshold
                    percentage = (projected_spending / budget.monthly_limit) * 100
                    return f"💡 This will use {percentage:.1f}% of your {expense.category} budget"

            return ""

        except Exception:
            return ""  # Silently handle budget check errors

    def get_expense_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive expense summary with additional insights.

        Returns:
            Dictionary with summary statistics and insights
        """
        expenses = self.get_expenses()

        if not expenses:
            return {
                "total_income": 0.0,
                "total_expenses": 0.0,
                "net_balance": 0.0,
                "this_month_income": 0.0,
                "this_month_expenses": 0.0,
                "this_month_balance": 0.0,
                "last_month_income": 0.0,
                "last_month_expenses": 0.0,
                "last_month_balance": 0.0,
                "daily_average": 0.0,
                "count": 0,
                "top_category": None,
                "insights": [],
            }

        # Basic calculations - separate income, expenses, and net balance
        total_income = ExpenseAggregator.total_income_only(expenses)
        total_expenses = abs(ExpenseAggregator.total_expenses_only(expenses))
        net_balance = ExpenseAggregator.total_amount(expenses)
        daily_avg = ExpenseAggregator.average_per_day(expenses)

        # This month calculations
        now = datetime.now()
        this_month_expenses = ExpenseFilter.by_month(expenses, now.year, now.month)
        this_month_income = ExpenseAggregator.total_income_only(this_month_expenses)
        this_month_expenses_amount = abs(
            ExpenseAggregator.total_expenses_only(this_month_expenses)
        )
        this_month_balance = ExpenseAggregator.total_amount(this_month_expenses)

        # Last month calculations
        last_month = now.replace(day=1) - timedelta(days=1)
        last_month_transactions = ExpenseFilter.by_month(
            expenses, last_month.year, last_month.month
        )
        last_month_income = ExpenseAggregator.total_income_only(last_month_transactions)
        last_month_expenses_amount = abs(
            ExpenseAggregator.total_expenses_only(last_month_transactions)
        )
        last_month_balance = ExpenseAggregator.total_amount(last_month_transactions)

        # Category breakdown
        category_totals = ExpenseAggregator.by_category(expenses)
        top_category = (
            max(category_totals.items(), key=lambda x: x[1])
            if category_totals
            else None
        )

        # Generate insights
        insights = self._generate_insights(
            expenses, this_month_balance, last_month_balance, category_totals
        )

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_balance": round(net_balance, 2),
            "this_month_income": round(this_month_income, 2),
            "this_month_expenses": round(this_month_expenses_amount, 2),
            "this_month_balance": round(this_month_balance, 2),
            "last_month_income": round(last_month_income, 2),
            "last_month_expenses": round(last_month_expenses_amount, 2),
            "last_month_balance": round(last_month_balance, 2),
            "daily_average": round(daily_avg, 2),
            "count": len(expenses),
            "top_category": top_category[0] if top_category else None,
            "top_category_amount": round(top_category[1], 2) if top_category else 0,
            "category_breakdown": {k: round(v, 2) for k, v in category_totals.items()},
            "insights": insights,
        }

    def _generate_insights(
        self,
        expenses: List[Expense],
        this_month: float,
        last_month: float,
        category_totals: Dict[str, float],
    ) -> List[str]:
        """
        Generate spending insights based on expense data.

        Args:
            expenses: List of all expenses
            this_month: This month's total spending
            last_month: Last month's total spending
            category_totals: Spending by category

        Returns:
            List of insight strings
        """
        insights = []

        # For spending insights, we need to separate expenses from the net total
        # Get just the expenses (negative amounts) for this analysis
        now = datetime.now()
        this_month_expenses = ExpenseFilter.by_month(expenses, now.year, now.month)
        this_month_spending = ExpenseAggregator.total_spending_absolute(
            this_month_expenses
        )

        last_month_date = now.replace(day=1) - timedelta(days=1)
        last_month_expenses = ExpenseFilter.by_month(
            expenses, last_month_date.year, last_month_date.month
        )
        last_month_spending = ExpenseAggregator.total_spending_absolute(
            last_month_expenses
        )

        # Month-over-month spending comparison
        if last_month_spending > 0:
            change = (
                (this_month_spending - last_month_spending) / last_month_spending
            ) * 100
            if change > 20:
                insights.append(f"📈 Spending increased {change:.1f}% from last month")
            elif change < -20:
                insights.append(
                    f"📉 Spending decreased {abs(change):.1f}% from last month"
                )

        # Category insights - focus on spending categories (negative amounts)
        if category_totals:
            # Filter to only expense categories (negative totals)
            expense_categories = {
                k: abs(v) for k, v in category_totals.items() if v < 0
            }

            if expense_categories:
                sorted_expense_categories = sorted(
                    expense_categories.items(), key=lambda x: x[1], reverse=True
                )

                # Top spending category
                if len(sorted_expense_categories) >= 1:
                    top_cat, top_amount = sorted_expense_categories[0]
                    total_expenses = sum(expense_categories.values())
                    percentage = (
                        (top_amount / total_expenses) * 100 if total_expenses > 0 else 0
                    )

                    if percentage > 40:
                        insights.append(
                            f"🎯 {top_cat} accounts for {percentage:.1f}% of your spending"
                        )

                # Balanced spending analysis
                if len(sorted_expense_categories) >= 3:
                    top_three_total = sum(
                        amount for _, amount in sorted_expense_categories[:3]
                    )
                    total_expenses = sum(expense_categories.values())
                    top_three_percentage = (
                        (top_three_total / total_expenses) * 100
                        if total_expenses > 0
                        else 0
                    )

                    if top_three_percentage < 60:
                        insights.append(
                            "⚖️ Your spending is well-distributed across categories"
                        )

        # Frequency insights
        recent_expenses = [
            exp
            for exp in expenses
            if (datetime.now() - datetime.strptime(exp.date, "%Y-%m-%d")).days <= 7
        ]

        if len(recent_expenses) > 10:
            insights.append("📊 You've been quite active with expenses this week")
        elif len(recent_expenses) < 3:
            insights.append("🎯 Light spending week - great job staying mindful!")

        return insights

    def get_category_analysis(self) -> Dict[str, Any]:
        """
        Get detailed category-based analysis.

        Returns:
            Dictionary with category analysis data
        """
        expenses = self.get_expenses()
        category_totals = ExpenseAggregator.by_category(expenses)

        # Calculate category statistics
        category_analysis = {}

        for category, total in category_totals.items():
            category_expenses = ExpenseFilter.by_category(expenses, category)

            category_analysis[category] = {
                "total": round(total, 2),
                "count": len(category_expenses),
                "average": (
                    round(total / len(category_expenses), 2) if category_expenses else 0
                ),
                "min": (
                    round(min(exp.amount for exp in category_expenses), 2)
                    if category_expenses
                    else 0
                ),
                "max": (
                    round(max(exp.amount for exp in category_expenses), 2)
                    if category_expenses
                    else 0
                ),
                "percentage_of_total": 0,  # Will be calculated below
            }

        # Calculate percentages
        total_spending = sum(category_totals.values())
        if total_spending > 0:
            for category in category_analysis:
                category_analysis[category]["percentage_of_total"] = round(
                    (category_analysis[category]["total"] / total_spending) * 100, 1
                )

        return category_analysis

    def get_monthly_trends(self, months: int = 6) -> Dict[str, Any]:
        """
        Get monthly spending trends.

        Args:
            months: Number of months to analyze (default: 6)

        Returns:
            Dictionary with monthly trend data
        """
        expenses = self.get_expenses()
        monthly_totals = ExpenseAggregator.by_month(expenses)

        # Get last N months
        end_date = datetime.now()
        trends = {}

        for i in range(months):
            date = end_date - timedelta(days=30 * i)
            month_key = date.strftime("%Y-%m")
            month_name = date.strftime("%B %Y")

            trends[month_name] = {
                "total": round(monthly_totals.get(month_key, 0.0), 2),
                "month_key": month_key,
            }

        return dict(reversed(list(trends.items())))  # Oldest first

    def search_expenses(
        self,
        query: str = "",
        category: str = "",
        start_date: str = "",
        end_date: str = "",
        min_amount: float = None,
        max_amount: float = None,
    ) -> List[Expense]:
        """
        Search expenses with multiple criteria.

        Args:
            query: Search term for description
            category: Category filter
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter

        Returns:
            List of matching expenses
        """
        expenses = self.get_expenses()

        # Apply filters step by step
        if query:
            expenses = ExpenseFilter.by_description_contains(expenses, query)

        if category:
            expenses = ExpenseFilter.by_category(expenses, category)

        if start_date and end_date:
            expenses = ExpenseFilter.by_date_range(expenses, start_date, end_date)

        if min_amount is not None and max_amount is not None:
            expenses = ExpenseFilter.by_amount_range(expenses, min_amount, max_amount)

        return expenses

    def get_data_service_status(self) -> Dict[str, Any]:
        """
        Get status information about the current data service.

        Returns:
            Dictionary with service status information
        """
        try:
            connection_result = self.data_service.test_connection()

            return {
                "service_type": "Mock Data" if self.use_mock_data else "Google Sheets",
                "connected": connection_result["success"],
                "message": connection_result["message"],
                "details": connection_result,
                "expense_count": len(self.get_expenses()),
                "last_cache_update": (
                    self._cache_last_updated.isoformat()
                    if self._cache_last_updated
                    else None
                ),
            }

        except Exception as e:
            return {
                "service_type": "Mock Data" if self.use_mock_data else "Google Sheets",
                "connected": False,
                "message": f"Error: {str(e)}",
                "details": {},
                "expense_count": 0,
                "last_cache_update": None,
            }

    def sync_data(self) -> Dict[str, Any]:
        """
        Sync data with the current service and refresh cache.

        Returns:
            Dictionary with sync results
        """
        try:
            result = self.data_service.sync_data()

            if result["success"]:
                self._invalidate_cache()  # Force cache refresh

            return result

        except Exception as e:
            return {"success": False, "message": f"Sync failed: {str(e)}"}

    def export_data(
        self, file_path: str = None, format_type: str = "csv"
    ) -> Tuple[bool, str]:
        """
        Export expense data to file.

        Args:
            file_path: Path to save file (optional)
            format_type: Export format ('csv', 'json')

        Returns:
            Tuple of (success, file_path_or_error_message)
        """
        try:
            if format_type.lower() == "csv" and hasattr(
                self.data_service, "export_to_csv"
            ):
                result_path = self.data_service.export_to_csv(
                    Path(file_path) if file_path else None
                )
                return True, result_path
            else:
                return False, f"Export format '{format_type}' not supported"

        except Exception as e:
            return False, f"Export failed: {str(e)}"
