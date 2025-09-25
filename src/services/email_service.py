#!/usr/bin/env python3
"""
Email Service for Spending Tracker

This service handles sending expense summaries via email with SMTP support.
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional, Tuple
import logging
from dataclasses import dataclass

from src.config.config_manager import ConfigManager
from src.models.expense import Expense


@dataclass
class EmailConfig:
    """Configuration for email settings."""

    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    from_email: str = ""
    from_name: str = "Spending Tracker"


class EmailService:
    """Service for sending expense summary emails."""

    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize the email service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config()
        self.logger = logging.getLogger(__name__)

    def _get_email_config(self) -> Optional[EmailConfig]:
        """
        Get email configuration from config file.

        Returns:
            EmailConfig object if configured, None otherwise
        """
        email_settings = self.config.get("email", {})

        # Check that required keys exist and have non-empty values (except smtp_port which is numeric)
        required_keys = ["smtp_server", "smtp_port", "username", "password"]
        if not all(key in email_settings for key in required_keys):
            return None

        # Check that string values are not empty
        if not all(
            (
                email_settings.get(key, "").strip()
                if key != "smtp_port"
                else email_settings.get(key)
            )
            for key in ["smtp_server", "username", "password"]
        ):
            return None

        return EmailConfig(
            smtp_server=email_settings["smtp_server"],
            smtp_port=email_settings["smtp_port"],
            username=email_settings["username"],
            password=email_settings["password"].replace(
                " ", ""
            ),  # Remove spaces from App Password
            use_tls=email_settings.get("use_tls", True),
            from_email=email_settings.get("from_email", email_settings["username"]),
            from_name=email_settings.get("from_name", "Spending Tracker"),
        )

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test email connection and authentication.

        Returns:
            Tuple of (success, message)
        """
        email_config = self._get_email_config()
        if not email_config:
            return False, "Email not configured. Please set up email settings first."

        # Check if recipients are configured
        recipients = self.get_recipients()
        if not recipients:
            return False, "No email recipients configured."

        try:
            # Create SMTP connection
            if email_config.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port)

            # Login
            server.login(email_config.username, email_config.password)
            server.quit()

            return (
                True,
                f"Email connection successful! Recipients configured: {len(recipients)}",
            )

        except smtplib.SMTPAuthenticationError:
            return (
                False,
                "Authentication failed. Please check your username and password.",
            )
        except smtplib.SMTPConnectError:
            return (
                False,
                f"Could not connect to SMTP server {email_config.smtp_server}:{email_config.smtp_port}",
            )
        except Exception as e:
            return False, f"Email connection failed: {str(e)}"

    def generate_summary_html(
        self, expenses: List[Expense], start_date: str, end_date: str
    ) -> str:
        """
        Generate HTML email content for expense summary.

        Args:
            expenses: List of expenses to summarise
            start_date: Start date for the summary period
            end_date: End date for the summary period

        Returns:
            HTML string for email body
        """
        if not expenses:
            return f"""
            <html>
            <body>
                <h2>Spending Summary ({start_date} to {end_date})</h2>
                <p>No expenses recorded for this period.</p>
            </body>
            </html>
            """

        # Calculate totals
        total_amount = sum(expense.amount for expense in expenses)
        currency_symbol = (
            self.config.get("data", {}).get("currency", {}).get("symbol", "£")
        )

        # Category breakdown
        category_totals = {}
        for expense in expenses:
            category = expense.category
            if category in category_totals:
                category_totals[category] += expense.amount
            else:
                category_totals[category] = expense.amount

        # Sort categories by amount (highest first)
        sorted_categories = sorted(
            category_totals.items(), key=lambda x: x[1], reverse=True
        )

        # Generate HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .total {{ font-size: 24px; color: #28a745; font-weight: bold; }}
                .summary-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .summary-table th, .summary-table td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                .summary-table th {{
                    background-color: #007bff;
                    color: white;
                    font-weight: bold;
                }}
                .summary-table tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .category-amount {{ text-align: right; font-weight: bold; }}
                .expense-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .expense-table th, .expense-table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                .expense-table th {{
                    background-color: #6c757d;
                    color: white;
                }}
                .expense-table tr:nth-child(even) {{ background-color: #f8f9fa; }}
                .amount {{ text-align: right; }}
                .footer {{ margin-top: 30px; color: #6c757d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>💰 Spending Summary</h1>
                <p><strong>Period:</strong> {start_date} to {end_date}</p>
                <p><strong>Total Expenses:</strong> {len(expenses)} transactions</p>
                <p class="total">Total Spent: {currency_symbol}{total_amount:.2f}</p>
            </div>

            <h2>📊 Category Breakdown</h2>
            <table class="summary-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Percentage</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
        """

        for category, amount in sorted_categories:
            percentage = (amount / total_amount) * 100
            count = sum(1 for exp in expenses if exp.category == category)
            html += f"""
                    <tr>
                        <td>{category}</td>
                        <td class="category-amount">{currency_symbol}{amount:.2f}</td>
                        <td>{percentage:.1f}%</td>
                        <td>{count}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>

            <h2>📋 Recent Expenses</h2>
            <table class="expense-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Show last 20 expenses or all if fewer than 20
        recent_expenses = sorted(expenses, key=lambda x: x.date, reverse=True)[:20]

        for expense in recent_expenses:
            html += f"""
                    <tr>
                        <td>{expense.format_date('%Y-%m-%d')}</td>
                        <td>{expense.description or '—'}</td>
                        <td>{expense.category}</td>
                        <td class="amount">{currency_symbol}{expense.amount:.2f}</td>
                    </tr>
            """

        html += f"""
                </tbody>
            </table>

            <div class="footer">
                <p>This report was generated automatically by Spending Tracker on {datetime.now().strftime('%Y-%m-%d at %H:%M')}.</p>
            </div>
        </body>
        </html>
        """

        return html

    def send_summary_email(
        self,
        recipients: List[str],
        expenses: List[Expense],
        start_date: str,
        end_date: str,
        subject_prefix: str = "",
        include_csv: bool = True,
    ) -> Tuple[bool, str]:
        """
        Send expense summary email to recipients.

        Args:
            recipients: List of email addresses
            expenses: List of expenses to summarise
            start_date: Start date for the summary period
            end_date: End date for the summary period
            subject_prefix: Optional prefix for email subject
            include_csv: Whether to include CSV attachment

        Returns:
            Tuple of (success, message)
        """
        email_config = self._get_email_config()
        if not email_config:
            return False, "Email not configured. Please set up email settings first."

        if not recipients:
            return False, "No email recipients configured."

        try:
            # Create message
            msg = MIMEMultipart("alternative")

            # Set email headers
            subject = f"{subject_prefix}Spending Summary ({start_date} to {end_date})"
            msg["Subject"] = subject
            msg["From"] = f"{email_config.from_name} <{email_config.from_email}>"
            msg["To"] = ", ".join(recipients)

            # Generate HTML content
            html_content = self.generate_summary_html(expenses, start_date, end_date)

            # Create plain text version
            total_amount = (
                sum(expense.amount for expense in expenses) if expenses else 0
            )
            currency_symbol = (
                self.config.get("data", {}).get("currency", {}).get("symbol", "£")
            )

            text_content = f"""
Spending Summary ({start_date} to {end_date})

Total Expenses: {len(expenses)} transactions
Total Spent: {currency_symbol}{total_amount:.2f}

This is an automated email from Spending Tracker.
Please view this email in HTML format for the full report.
            """

            # Attach both text and HTML versions
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            # Add CSV attachment if requested
            if include_csv and expenses:
                csv_data = self._generate_csv_attachment(expenses)
                if csv_data:
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(csv_data.encode("utf-8"))
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        "Content-Disposition",
                        f'attachment; filename="expenses_{start_date}_to_{end_date}.csv"',
                    )
                    msg.attach(attachment)

            # Send email
            if email_config.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port)

            server.login(email_config.username, email_config.password)
            server.send_message(msg)
            server.quit()

            self.logger.info(
                f"Summary email sent successfully to {len(recipients)} recipients"
            )
            return (
                True,
                f"Email sent successfully to {len(recipients)} recipient{'s' if len(recipients) > 1 else ''}!",
            )

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _generate_csv_attachment(self, expenses: List[Expense]) -> str:
        """
        Generate CSV content for email attachment.

        Args:
            expenses: List of expenses to export

        Returns:
            CSV content as string
        """
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Date", "Amount", "Category", "Description"])

        # Write expenses (sorted by date, newest first)
        sorted_expenses = sorted(expenses, key=lambda x: x.date, reverse=True)
        for expense in sorted_expenses:
            writer.writerow(
                [expense.date, expense.amount, expense.category, expense.description]
            )

        return output.getvalue()

    def get_recipients(self) -> List[str]:
        """
        Get email recipients from configuration.

        Returns:
            List of email addresses
        """
        email_settings = self.config.get("email", {})
        return email_settings.get("recipients", [])

    def update_recipients(self, recipients: List[str]) -> bool:
        """
        Update email recipients in configuration.

        Args:
            recipients: List of email addresses

        Returns:
            True if successful
        """
        try:
            config = self.config_manager.get_config()
            if "email" not in config:
                config["email"] = {}

            config["email"]["recipients"] = recipients
            self.config_manager.save_config(config)
            self.config = config
            return True

        except Exception as e:
            self.logger.error(f"Failed to update recipients: {str(e)}")
            return False
