# tests/test_arguments.py
import logging
import unittest
from pathlib import Path

from src.om_cli.handlers.arguments_handler import (
    collect_arguments,
    convert_arguments_to_operation_and_om_parameters,
    parse_arguments,
    update_log_level,
)
from src.om_cli.logger import logger, setup_logger
from src.om_cli.models.om_parameter import OMParameterType
from src.om_cli.services.custom_components_processing import CustomComponents


class TestArguments(unittest.TestCase):
    SCRIPT_PATH = Path(__file__).parents[1]
    CUSTOM_PATH = f"{SCRIPT_PATH}/custom"
    OM_TREE_PATH = f"{SCRIPT_PATH}/custom/test_resources/mock_om_tree.json"
    API_RESPONSES_PATH = f"{SCRIPT_PATH}/custom/test_resources/mock_api_responses.json"

    def test_set_debug_log_level(self):
        # Test updating log level

        setup_logger("om_cli")

        self.assertEqual(logger.level, logging.DEBUG)

        found_stdout = False
        for handler in logger.handlers:
            if handler.name == "stdout":
                found_stdout = True
                self.assertEqual(handler.level, logging.INFO)
                break

        self.assertTrue(found_stdout)

        args = ["-l", "DEBUG"]
        collected_args = collect_arguments(args)

        self.assertIsNotNone(collected_args.log_level)
        update_log_level(collected_args.log_level)

        for handler in logger.handlers:
            if handler.name == "stdout":
                self.assertEqual(handler.level, logging.DEBUG)
                break

    def test_get_registry_command_parsing(self):
        # Test parsing operation with arguments
        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )
        om_tree = custom_components.get_om_tree()

        args = ["-o", "get_registry", 'registry_id="registry-1"']
        collected_args = collect_arguments(args)
        (operation, om_parameters) = convert_arguments_to_operation_and_om_parameters(
            collected_args, om_tree
        )

        self.assertIsNotNone(operation)
        self.assertEqual(operation.operation_id, "get_registry")
        self.assertEqual(len(om_parameters), 1)
        self.assertEqual(om_parameters[0].name, "registry_id")
        self.assertEqual(om_parameters[0].type, OMParameterType.STRING)
        self.assertEqual(om_parameters[0].value, "registry-1")

    def test_use_custom_om_tree_command_parsing(self):
        om_tree_file_path = f"{self.SCRIPT_PATH}/custom/test_resources/mock_om_tree.json"
        args = ["-t", om_tree_file_path]
        parse_arguments_result = parse_arguments(args)
        self.assertEqual(parse_arguments_result.get("om_tree_file_path", ""), om_tree_file_path)

    def test_use_internal_mock_responses_command_parsing(self):
        mock_api_responses_file_path = f"{self.API_RESPONSES_PATH}"
        args = ["-m", mock_api_responses_file_path]
        parse_arguments_result = parse_arguments(args)
        read_mock_api_responses_file_path = parse_arguments_result.get(
            "mock_api_responses_file_path", ""
        )
        self.assertEqual(read_mock_api_responses_file_path, self.API_RESPONSES_PATH)


if __name__ == "__main__":
    unittest.main()
