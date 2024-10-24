# src/om_cli/logger.py

"""Logging configuration"""

import datetime
import json
import logging
import logging.config
import logging.handlers
import os

from syslog_rfc5424_formatter import RFC5424Formatter

log_config = "src/om_cli/logging.json"
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


def load_logging_config():
    """
    Loads the logging configuration from a JSON file.

    Returns:
        dict: The logging configuration dictionary.
    """
    try:
        with open(log_config, encoding="utf-8") as file:
            config_dict = json.load(file)

            # Custom filters to log debug and info messages to stdout, and warning, error and critical messages to stderr
            config_dict["filters"] = {
                "info_debug_filter": {"()": InfoDebugFilter},
                "warning_error_filter": {"()": WarningErrorFilter},
            }

            config_dict["formatters"]["syslog"] = {
                "()": CustomRFC5424Formatter,
                "format": "%(message)s",
            }

            # Generate a unique file name with a timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_name = f"logs/logfile_{timestamp}.log"

            # Ensure the logs directory exists
            os.makedirs(os.path.dirname(log_file_name), exist_ok=True)

            # Add file handler to the configuration
            config_dict["handlers"]["file"] = {
                "class": "logging.FileHandler",
                "formatter": "syslog",
                "filename": log_file_name,
                "mode": "a",
                "level": "DEBUG",
            }

            # Ensure the file handler is included in the loggers
            for logger_name in config_dict["loggers"]:
                config_dict["loggers"][logger_name]["handlers"].append("file")

            return config_dict
    except FileNotFoundError:
        print(f"Logging configuration file {log_config} not found.")
        return {}


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
    config_dict = load_logging_config()
    logging.config.dictConfig(config_dict)
    logger = logging.getLogger(logger_name)
    # logger.setLevel(level)
    logger.debug("Logging configuration %s loaded", logger_name)

    # Set the level for stdout and stderr handlers based on the provided level
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            handler.setLevel(level)

    return logger


def get_logger():
    """
    Get the logger instance.

    Returns:
        logging.Logger: The logger instance.
    """
    global logger
    if logger is None:
        logger = setup_logger()
    return logger


def update_terminal_log_level(level):
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

    level_name = logging._levelToName.get(level, "Level %s" % level)
    logger.debug(f"Updated terminal log level to {level_name}")
