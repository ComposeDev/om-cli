# src/om_cli/logger.py

"""Logging configuration"""

import datetime
import json
import logging
import logging.config
import logging.handlers
import os
import sys
from typing import Dict, Optional

from syslog_rfc5424_formatter import RFC5424Formatter

current_dir = os.path.dirname(os.path.abspath(__file__))
log_config = os.path.join(current_dir, "logging.json")
logger = None


class CustomRFC5424Formatter(RFC5424Formatter):
    def format(self, record):
        return super().format(record)


class InfoDebugFilter(logging.Filter):
    def filter(self, record):
        return record.levelno in (logging.INFO, logging.DEBUG)


class WarningErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.WARNING


class SysLogHandler(logging.handlers.SysLogHandler):
    """A SysLogHandler that tries multiple socket paths and handles failures gracefully."""

    SYSLOG_PATHS = [
        '/dev/log',         # Linux
        '/var/run/syslog',  # macOS
        '/var/run/log',     # Alternative Linux path
        'localhost:514',    # Default syslog address
    ]

    @classmethod
    def get_available_socket(cls) -> Optional[str]:
        """Try different syslog socket paths and return the first working one."""
        for path in cls.SYSLOG_PATHS:
            if os.path.exists(path):
                try:
                    # Test if we can actually connect to the socket
                    handler = logging.handlers.SysLogHandler(address=path)
                    handler.close()
                    return path
                except (OSError, ConnectionError):
                    continue
        return None


def load_logging_config() -> Dict:
    """
    Loads the logging configuration from a JSON file with enhanced error handling
    and syslog configuration.

    Returns:
        dict: The logging configuration dictionary.
    """
    try:
        with open(log_config, encoding="utf-8") as file:
            config_dict = json.load(file)

            # Custom filters configuration
            config_dict["filters"] = {
                "info_debug_filter": {"()": InfoDebugFilter},
                "warning_error_filter": {"()": WarningErrorFilter},
            }

            # RFC5424 formatter configuration
            config_dict["formatters"]["syslog"] = {
                "()": CustomRFC5424Formatter,
                "format": "%(message)s",
            }

            # Generate timestamped log file name
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_name = f"logs/logfile_{timestamp}.log"
            os.makedirs(os.path.dirname(log_file_name), exist_ok=True)

            # Configure file handler
            config_dict["handlers"]["file"] = {
                "class": "logging.FileHandler",
                "formatter": "syslog",
                "filename": log_file_name,
                "mode": "a",
                "level": "DEBUG",
            }

            # Configure robust syslog handler
            syslog_path = SysLogHandler.get_available_socket()
            if syslog_path:
                config_dict["handlers"]["syslog"] = {
                    "class": "om_cli.logger.SysLogHandler",
                    "formatter": "syslog",
                    "address": syslog_path,
                    "level": "DEBUG"
                }
            else:
                # Remove syslog handler if no socket is available
                if "syslog" in config_dict["handlers"]:
                    del config_dict["handlers"]["syslog"]
                    # Remove syslog from all loggers' handlers
                    for logger_name in config_dict["loggers"]:
                        handlers = config_dict["loggers"][logger_name]["handlers"]
                        if "syslog" in handlers:
                            handlers.remove("syslog")

            # Ensure file handler is included in all loggers
            for logger_name in config_dict["loggers"]:
                if "file" not in config_dict["loggers"][logger_name]["handlers"]:
                    config_dict["loggers"][logger_name]["handlers"].append("file")

            return config_dict

    except FileNotFoundError:
        print(f"Logging configuration file {log_config} not found.", file=sys.stderr)
        return {
            "version": 1,
            "handlers": {
                "stderr": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "stream": "ext://sys.stderr",
                    "level": "WARNING"
                }
            },
            "formatters": {
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "root": {
                "level": "WARNING",
                "handlers": ["stderr"]
            }
        }


def setup_logger(logger_name: str = "om_cli", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up the logger with the given name and level.

    Args:
        logger_name (str, optional): The name of the logger. Defaults to "om_cli".
        level (int, optional): The logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: The configured logger.
    """
    global logger
    try:
        config_dict = load_logging_config()
        logging.config.dictConfig(config_dict)
        logger = logging.getLogger(logger_name)
        logger.debug("Logging configuration %s loaded", logger_name)

        # Set the level for stdout and stderr handlers
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setLevel(level)

        return logger
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        logger = logging.getLogger(logger_name)
        logger.error("Failed to load logging configuration: %s", str(e))
        return logger


def get_logger() -> logging.Logger:
    """
    Get the logger instance.

    Returns:
        logging.Logger: The logger instance.
    """
    global logger
    if logger is None:
        logger = setup_logger()
    return logger


def update_terminal_log_level(level: int) -> None:
    """
    Update the log level for terminal handlers (stdout and stderr).

    Args:
        level (int): The logging level to set for terminal handlers.
    """
    global logger
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            handler.setLevel(level)

    level_name = logging._levelToName.get(level, f"Level {level}")
    logger.debug("Updated terminal log level to %s", level_name)
