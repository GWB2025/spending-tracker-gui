#!/usr/bin/env python3
"""
Configuration Manager for Spending Tracker

This module handles loading and managing configuration from YAML files.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration from YAML files."""

    def __init__(self, config_path: str = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the config file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._config = None
        self._last_modified = None

    def get_config(self) -> Dict[str, Any]:
        """
        Load and return the configuration.

        Returns:
            Dictionary containing the full configuration.
        """
        # Check if we need to reload the config
        if self._config is None or self._config_needs_reload():
            self._load_config()
        return self._config
    
    def _config_needs_reload(self) -> bool:
        """Check if config needs to be reloaded based on file modification time."""
        try:
            current_modified = os.path.getmtime(self.config_path)
            return self._last_modified != current_modified
        except (OSError, FileNotFoundError):
            return True

    def _load_config(self):
        """Load configuration from the YAML file."""
        try:
            # Track modification time for caching
            self._last_modified = os.path.getmtime(self.config_path)
            
            with open(self.config_path, "r", encoding="utf-8") as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
        except OSError as e:
            raise OSError(f"Error reading configuration file: {e}")

    def reload_config(self):
        """Reload the configuration from file."""
        self._config = None
        self._load_config()

    def get_app_config(self) -> Dict[str, Any]:
        """Get application-specific configuration."""
        return self.get_config().get("app", {})

    def get_google_sheets_config(self) -> Dict[str, Any]:
        """Get Google Sheets configuration."""
        return self.get_config().get("google_sheets", {})

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return self.get_config().get("ui", {})

    def get_data_config(self) -> Dict[str, Any]:
        """Get data configuration."""
        return self.get_config().get("data", {})

    def update_spreadsheet_id(self, spreadsheet_id: str):
        """
        Update the Google Sheets spreadsheet ID in the configuration.

        Args:
            spreadsheet_id: The new spreadsheet ID to save.
        """
        config = self.get_config()
        config["google_sheets"]["spreadsheet_id"] = spreadsheet_id

        # Save back to file
        with open(self.config_path, "w", encoding="utf-8") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)

        # Update cached config
        self._config = config

    def save_config(self, config: Dict[str, Any] = None):
        """
        Save the configuration to file.

        Args:
            config: Configuration dictionary to save. If None, saves current cached config.
        """
        if config is None:
            config = self._config

        if config is None:
            raise ValueError("No configuration to save")

        # Save to file
        with open(self.config_path, "w", encoding="utf-8") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)

        # Update cached config
        self._config = config
