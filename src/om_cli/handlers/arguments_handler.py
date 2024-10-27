# src/om_cli/handlers/arguments_handler.py

"""
This module contains the argument parsing logic for the OM CLI.
"""

import argparse
import logging
import re
import sys
from pathlib import Path

from consolemenu import Screen

from src.om_cli.helpers.operation_tree_helpers import get_operation_by_id
from src.om_cli.helpers.text_helpers import colorize_text
from src.om_cli.logger import logger, update_terminal_log_level
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.om_tree import OMTree
from src.om_cli.services.parameter_processing import verify_arguments

SCRIPT_PATH = Path(__file__).resolve().parents[3]


def update_log_level(log_level: str) -> bool:
    """
    Update the log level of the logger.

    Args:
        log_level (str): The desired log level. Valid values are "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

    Returns:
        bool: True if the log level was successfully updated, False otherwise.
    """

    if log_level:
        if log_level.upper() in {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }:
            new_log_level_value = getattr(logging, log_level.upper())
            update_terminal_log_level(new_log_level_value)
            return True
        else:
            logger.warning(
                "Invalid log level provided %s. Using default log level. (INFO)",
                log_level,
            )
            return False
    return False


def collect_arguments(arguments=None):
    """
    Collects and parses command line arguments for the OM CLI.

    Args:
        arguments (list): List of command line arguments to pars. Used for testing. (default: None).

    Returns:
        argparse.Namespace: An object containing the parsed command line arguments.

    """
    parser = argparse.ArgumentParser(description="OM CLI")

    parser.add_argument(
        "-l",
        "--log_level",
        type=str,
        help="The log level to use for the CLI, e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL, INFO by default.",
    )
    parser.add_argument(
        "-c",
        "--custom_path",
        type=str,
        help="The path to the custom configuration directory.",
    )
    parser.add_argument(
        "-t",
        "--tree_path",
        type=str,
        help="Used when you want to load the OMTree configuration from a non default path.",
    )
    parser.add_argument(
        "-m",
        "--mock_api_responses_file_path",
        type=str,
        help="The path to the mock API responses file.",
    )
    parser.add_argument(
        "-g",
        "--generate_tree",
        action=argparse.BooleanOptionalAction,
        help="If set, the CLI will generate a new OMTree configuration file from the current OMTree.",
    )
    parser.add_argument("-o", "--operation", type=str, help="The operation to execute.")
    parser.add_argument(
        "-s",
        "--skip_looping",
        action=argparse.BooleanOptionalAction,
        help="If set, the CLI will skip action looping during operation execution.",
    )
    parser.add_argument("params", nargs="*", type=str, help="Parameters for the operation.")

    return parser.parse_args(arguments)


def convert_arguments_to_operation_and_om_parameters(arguments_object, om_tree: OMTree):
    """
    Converts the arguments object and operation tree into an operation and OM parameters.

    Args:
        arguments_object: The object containing the command and parameters.
        om_tree (OMTree): The configuration containing the tree structure representing the available operations.

    Returns:
        A tuple containing the operation and an OMParameterList.

    Raises:
        Exception: If the command is not a valid command or if one or more parameters are invalid.
    """

    if not arguments_object.operation:
        return (None, OMParameterList())

    operation = get_operation_by_id(om_tree.operations, arguments_object.operation)
    if not operation:
        raise ValueError(f"{arguments_object.operation} is not a valid operation")

    try:
        # Use dictionary comprehension to split parameters and strip outer quotes
        splitted_arguments = {
            param.split("=", 1)[0]: re.sub(r'(^[\'"]|[\'"]$)', "", param.split("=", 1)[1])
            for param in arguments_object.params
            if "=" in param
        }

        if not splitted_arguments:
            logger.error("No valid parameters found.")
            Screen().input(colorize_text("\nPress enter to exit", "red"))
            sys.exit(1)
    except Exception as ex:
        logger.error("Invalid parameters: %s", ex)
        sys.exit(1)

    om_parameters = verify_arguments(splitted_arguments, operation)
    logger.debug("Verified parameters: %s", om_parameters)

    return (operation, om_parameters)


def parse_arguments(arguments=None):
    """
    Parses the command-line arguments and converts them into an operation and OM parameters.

    Args:
        om_tree: The configuration containing the tree structure representing the available operations..

    Returns:
        A tuple containing the resulting operation, OM parameters and skip_looping value.

    """
    logger.debug("Starting to parse command-line arguments...")
    argument_parser_result = collect_arguments(arguments)

    if argument_parser_result.log_level:
        update_log_level(argument_parser_result.log_level)

    skip_looping = bool(argument_parser_result.skip_looping)
    if skip_looping:
        logger.debug("skip_looping has been activated")

    generate_tree = bool(argument_parser_result.generate_tree)

    om_tree_file_path = ""
    if argument_parser_result.tree_path:
        om_tree_file_path = argument_parser_result.tree_path

    custom_path = ""
    if argument_parser_result.custom_path:
        custom_path = argument_parser_result.custom_path

    mock_api_responses_file_path = ""
    if argument_parser_result.mock_api_responses_file_path:
        mock_api_responses_file_path = argument_parser_result.mock_api_responses_file_path

    logger.debug("Finished parsing command-line arguments.")
    return {
        "arguments": argument_parser_result,
        "skip_looping": skip_looping,
        "generate_tree": generate_tree,
        "custom_path": custom_path,
        "om_tree_file_path": om_tree_file_path,
        "mock_api_responses_file_path": mock_api_responses_file_path,
    }
