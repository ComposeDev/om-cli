# src/om_cli/__main__.py
"""OM CLI"""

from consolemenu import Screen

from src.om_cli.handlers.arguments_handler import (
    convert_arguments_to_operation_and_om_parameters,
    parse_arguments,
)
from src.om_cli.handlers.menu_handler import run_menu
from src.om_cli.helpers.text_helpers import colorize_text
from src.om_cli.logger import logger
from src.om_cli.services.custom_components_processing import CustomComponents
from src.om_cli.services.operation_processing import process_operation
from src.om_cli.services.operation_tree_generator import (
    generate_json_config_from_operation_tree,
)


def main():
    """
    Main function that parses command-line arguments or presents a menu.
    """

    logger.debug("Starting OM CLI...")
    parse_arguments_result = parse_arguments()

    if not parse_arguments_result.get("custom_path"):
        logger.error("Custom path is missing.")
        Screen().input(colorize_text("\nPress enter to exit", "red"))
        exit(1)

    custom_components = CustomComponents.load_custom_components(
        parse_arguments_result.get("custom_path"),
        parse_arguments_result.get("om_tree_file_path"),
        parse_arguments_result.get("mock_api_responses_file_path"),
    )

    om_tree = custom_components.get_om_tree()

    operation, argument_parameters = convert_arguments_to_operation_and_om_parameters(
        parse_arguments_result.get("arguments"), om_tree
    )

    if parse_arguments_result.get("generate_tree"):
        logger.debug("generate_tree has been activated")
        om_tree = generate_json_config_from_operation_tree(om_tree, "temp_om_tree.json")
        logger.info("Generated a new OMTree config file: temp_om_tree.json")

    if operation:
        process_operation(
            operation,
            argument_parameters,
            custom_components,
            parse_arguments_result.get("skip_looping"),
        )
    else:
        run_menu(custom_components)


if __name__ == "__main__":
    main()
