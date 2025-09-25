#!/usr/bin/env python3
"""
Email Scheduler Service for Spending Tracker

This service handles scheduling and sending automated email reports.
"""

import threading
import time
from datetime import datetime, timedelta, date
from typing import List, Optional, Callable, Tuple
import logging
from dataclasses import dataclass
import schedule

from src.config.config_manager import ConfigManager
from src.services.email_service import EmailService
from src.controllers.expense_controller import ExpenseController


@dataclass
class ScheduleConfig:
    """Configuration for email scheduling."""

    enabled: bool
    send_monthly: bool
    day_of_month: int
    hour: int
    minute: int
    subject_prefix: str
    include_csv_attachment: bool


class EmailScheduler:
    """Service for scheduling automated email reports."""

    def __init__(
        self,
        config_manager: ConfigManager = None,
        expense_controller: ExpenseController = None,
    ):
        """
        Initialize the email scheduler.

        Args:
            config_manager: Configuration manager instance
            expense_controller: Expense controller for data access
        """
        self.config_manager = config_manager or ConfigManager()
        self.expense_controller = expense_controller
        self.email_service = EmailService(config_manager)
        self.logger = logging.getLogger(__name__)

        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        # Callback for status updates
        self.status_callback: Optional[Callable[[str], None]] = None

        # Load schedule configuration
        self._load_schedule_config()

    def _load_schedule_config(self) -> None:
        """Load schedule configuration from config file."""
        config = self.config_manager.get_config()
        schedule_settings = config.get("email", {}).get("schedule", {})

        self.schedule_config = ScheduleConfig(
            enabled=schedule_settings.get("enabled", False),
            send_monthly=schedule_settings.get("send_monthly", True),
            day_of_month=schedule_settings.get("day_of_month", 1),
            hour=schedule_settings.get("hour", 9),
            minute=schedule_settings.get("minute", 0),
            subject_prefix=schedule_settings.get("subject_prefix", "[Monthly Report] "),
            include_csv_attachment=schedule_settings.get(
                "include_csv_attachment", True
            ),
        )

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback function for status updates.

        Args:
            callback: Function to call with status messages
        """
        self.status_callback = callback

    def _notify_status(self, message: str) -> None:
        """
        Notify status to callback if set.

        Args:
            message: Status message
        """
        if self.status_callback:
            self.status_callback(message)
        self.logger.info(message)

    def is_running(self) -> bool:
        """
        Check if scheduler is currently running.

        Returns:
            True if scheduler is active
        """
        return self._running

    def start_scheduler(self) -> bool:
        """
        Start the email scheduler in a background thread.

        Returns:
            True if scheduler started successfully
        """
        if self._running:
            self._notify_status("Email scheduler is already running")
            return True

        if not self.schedule_config.enabled:
            self._notify_status("Email scheduling is disabled in configuration")
            return False

        try:
            # Clear any existing schedules
            schedule.clear()

            # Set up monthly schedule
            if self.schedule_config.send_monthly:
                # Schedule to run daily, but only send emails on the specified day of month
                schedule.every().day.at(
                    f"{self.schedule_config.hour:02d}:{self.schedule_config.minute:02d}"
                ).do(self._check_and_send_monthly_report)

                self._notify_status(
                    f"Scheduled monthly reports for day {self.schedule_config.day_of_month} at {self.schedule_config.hour:02d}:{self.schedule_config.minute:02d}"
                )

            # Start scheduler thread
            self._stop_event.clear()
            self._scheduler_thread = threading.Thread(
                target=self._run_scheduler, daemon=True
            )
            self._scheduler_thread.start()
            self._running = True

            self._notify_status("Email scheduler started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start email scheduler: {str(e)}")
            self._notify_status(f"Failed to start scheduler: {str(e)}")
            return False

    def stop_scheduler(self) -> bool:
        """
        Stop the email scheduler.

        Returns:
            True if scheduler stopped successfully
        """
        if not self._running:
            self._notify_status("Email scheduler is not running")
            return True

        try:
            self._stop_event.set()
            self._running = False

            # Clear scheduled jobs
            schedule.clear()

            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=5.0)

            self._notify_status("Email scheduler stopped")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop email scheduler: {str(e)}")
            self._notify_status(f"Failed to stop scheduler: {str(e)}")
            return False

    def _run_scheduler(self) -> None:
        """Run the scheduler in a background thread."""
        while not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler thread: {str(e)}")
                self._notify_status(f"Scheduler error: {str(e)}")
                time.sleep(60)

    def _check_and_send_monthly_report(self) -> None:
        """Check if today is the scheduled day and send monthly report if so."""
        today = date.today()

        # Check if today is the scheduled day of the month
        if today.day != self.schedule_config.day_of_month:
            return

        # Check if we've already sent a report this month
        if self._was_report_sent_this_month():
            return

        try:
            self._notify_status(
                f"Sending scheduled monthly report for {today.strftime('%B %Y')}"
            )
            success, message = self.send_monthly_report()

            if success:
                self._record_report_sent()
                self._notify_status(f"Monthly report sent successfully: {message}")
            else:
                self._notify_status(f"Failed to send monthly report: {message}")

        except Exception as e:
            error_msg = f"Error sending scheduled monthly report: {str(e)}"
            self.logger.error(error_msg)
            self._notify_status(error_msg)

    def _was_report_sent_this_month(self) -> bool:
        """
        Check if a report was already sent this month.

        Returns:
            True if report was already sent
        """
        config = self.config_manager.get_config()
        email_settings = config.get("email", {})
        last_sent = email_settings.get("last_monthly_report_sent")

        if not last_sent:
            return False

        try:
            last_sent_date = datetime.fromisoformat(last_sent).date()
            today = date.today()

            # Check if last sent date is in the same month and year
            return (
                last_sent_date.year == today.year
                and last_sent_date.month == today.month
            )
        except Exception:
            return False

    def _record_report_sent(self) -> None:
        """Record that a monthly report was sent today."""
        try:
            config = self.config_manager.get_config()
            if "email" not in config:
                config["email"] = {}

            config["email"]["last_monthly_report_sent"] = date.today().isoformat()
            self.config_manager.save_config(config)

        except Exception as e:
            self.logger.error(f"Failed to record report sent date: {str(e)}")

    def send_monthly_report(
        self, custom_recipients: List[str] = None
    ) -> Tuple[bool, str]:
        """
        Send a monthly expense report immediately.

        Args:
            custom_recipients: Optional custom recipient list

        Returns:
            Tuple of (success, message)
        """
        if not self.expense_controller:
            return False, "Expense controller not available"

        try:
            # Calculate date range for last month
            today = date.today()
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)

            start_date = first_day_last_month.strftime("%Y-%m-%d")
            end_date = last_day_last_month.strftime("%Y-%m-%d")

            # Get expenses for the period
            all_expenses = self.expense_controller.get_expenses()
            period_expenses = [
                expense
                for expense in all_expenses
                if expense.is_in_date_range(start_date, end_date)
            ]

            # Get recipients
            recipients = custom_recipients or self.email_service.get_recipients()
            if not recipients:
                return False, "No email recipients configured"

            # Send email
            return self.email_service.send_summary_email(
                recipients=recipients,
                expenses=period_expenses,
                start_date=start_date,
                end_date=end_date,
                subject_prefix=self.schedule_config.subject_prefix,
                include_csv=self.schedule_config.include_csv_attachment,
            )

        except Exception as e:
            error_msg = f"Failed to send monthly report: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def send_custom_report(
        self, start_date: str, end_date: str, recipients: List[str] = None
    ) -> Tuple[bool, str]:
        """
        Send a custom expense report for a specific date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            recipients: Optional custom recipient list

        Returns:
            Tuple of (success, message)
        """
        if not self.expense_controller:
            return False, "Expense controller not available"

        try:
            # Get expenses for the period
            all_expenses = self.expense_controller.get_expenses()
            period_expenses = [
                expense
                for expense in all_expenses
                if expense.is_in_date_range(start_date, end_date)
            ]

            # Get recipients
            recipient_list = recipients or self.email_service.get_recipients()
            if not recipient_list:
                return False, "No email recipients configured"

            # Send email
            return self.email_service.send_summary_email(
                recipients=recipient_list,
                expenses=period_expenses,
                start_date=start_date,
                end_date=end_date,
                subject_prefix="[Custom Report] ",
                include_csv=True,
            )

        except Exception as e:
            error_msg = f"Failed to send custom report: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def update_schedule_config(
        self,
        enabled: bool = None,
        day_of_month: int = None,
        hour: int = None,
        minute: int = None,
        subject_prefix: str = None,
        include_csv: bool = None,
    ) -> bool:
        """
        Update schedule configuration.

        Args:
            enabled: Whether scheduling is enabled
            day_of_month: Day of month to send (1-31)
            hour: Hour to send (0-23)
            minute: Minute to send (0-59)
            subject_prefix: Subject prefix for emails
            include_csv: Whether to include CSV attachment

        Returns:
            True if update was successful
        """
        try:
            config = self.config_manager.get_config()
            if "email" not in config:
                config["email"] = {}
            if "schedule" not in config["email"]:
                config["email"]["schedule"] = {}

            schedule_config = config["email"]["schedule"]

            if enabled is not None:
                schedule_config["enabled"] = enabled
            if day_of_month is not None:
                schedule_config["day_of_month"] = max(1, min(31, day_of_month))
            if hour is not None:
                schedule_config["hour"] = max(0, min(23, hour))
            if minute is not None:
                schedule_config["minute"] = max(0, min(59, minute))
            if subject_prefix is not None:
                schedule_config["subject_prefix"] = subject_prefix
            if include_csv is not None:
                schedule_config["include_csv_attachment"] = include_csv

            # Save configuration
            self.config_manager.save_config(config)

            # Reload configuration
            self._load_schedule_config()

            # Restart scheduler if it was running
            if self._running:
                self.stop_scheduler()
                time.sleep(1)  # Brief pause
                self.start_scheduler()

            return True

        except Exception as e:
            self.logger.error(f"Failed to update schedule configuration: {str(e)}")
            return False

    def get_next_scheduled_time(self) -> Optional[str]:
        """
        Get the next scheduled email time.

        Returns:
            Next scheduled time as string, or None if not scheduled
        """
        if not self.schedule_config.enabled:
            return None

        try:
            today = date.today()
            current_time = datetime.now().time()
            scheduled_time = (
                datetime.now()
                .replace(
                    hour=self.schedule_config.hour,
                    minute=self.schedule_config.minute,
                    second=0,
                    microsecond=0,
                )
                .time()
            )

            # Determine next scheduled date
            if today.day < self.schedule_config.day_of_month:
                # This month
                next_date = today.replace(day=self.schedule_config.day_of_month)
            elif (
                today.day == self.schedule_config.day_of_month
                and current_time < scheduled_time
            ):
                # Today, but before scheduled time
                next_date = today
            else:
                # Next month
                if today.month == 12:
                    next_date = date(
                        today.year + 1, 1, self.schedule_config.day_of_month
                    )
                else:
                    try:
                        next_date = today.replace(
                            month=today.month + 1, day=self.schedule_config.day_of_month
                        )
                    except ValueError:
                        # Handle months with fewer days
                        import calendar

                        next_month = today.month + 1
                        next_year = today.year
                        if next_month > 12:
                            next_month = 1
                            next_year += 1
                        max_day = calendar.monthrange(next_year, next_month)[1]
                        day = min(self.schedule_config.day_of_month, max_day)
                        next_date = date(next_year, next_month, day)

            next_datetime = datetime.combine(next_date, scheduled_time)
            return next_datetime.strftime("%Y-%m-%d at %H:%M")

        except Exception as e:
            self.logger.error(f"Failed to calculate next scheduled time: {str(e)}")
            return None
