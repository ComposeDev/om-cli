# tests/test_actions.py

# import os
import json
import os
import pwd
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch  # ANY,

from requests.models import Response

from src.om_cli.handlers.arguments_handler import collect_arguments, update_log_level
from src.om_cli.helpers.operation_tree_helpers import get_operation_by_id
from src.om_cli.logger import setup_logger
from src.om_cli.models.om_parameter import OMParameter
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.services.custom_components_processing import CustomComponents
from src.om_cli.services.operation_processing import Screen, process_operation


class TestActions(unittest.TestCase):
    # Get the project base path from the current file path
    SCRIPT_PATH = Path(__file__).parents[1]
    RUN_MODULE_COMMAND = f"cd {Path(SCRIPT_PATH)} && {sys.executable} -m src.om_cli -s -o"
    CUSTOM_PATH = f"{SCRIPT_PATH}/custom"
    OM_TREE_PATH = f"{SCRIPT_PATH}/custom/test_resources/mock_om_tree.json"
    API_RESPONSES_PATH = f"{SCRIPT_PATH}/custom/test_resources/mock_api_responses.json"
    BASE_URL = "http://127.0.0.1:8080"

    @staticmethod
    def mock_requests_get(url, headers=None, params=None, timeout=None):
        # Globally mock the requests.get function in one place to return predefined responses without actually making an API request
        response = Mock(spec=Response)
        response.json = TestActions.get_predefined_responses(url)
        response.text = json.dumps(response.json)
        response.json = Mock(return_value=response.json)
        response.headers = {"Content-Type": "application/json"}
        response.status_code = 200
        return response

    @staticmethod
    def mock_requests_post(url, headers=None, params=None, timeout=None, data=None):
        # Globally mock the requests.post function in one place to return predefined responses without actually making an API request
        response = Mock(spec=Response)
        response.json = TestActions.get_predefined_responses(url)
        response.text = json.dumps(response.json)
        response.json = Mock(return_value=response.json)
        response.headers = {"Content-Type": "application/json"}
        response.status_code = 200
        return response

    @staticmethod
    def get_predefined_responses(url):
        """
        This function will load a json file containing all api responses in json from the predefined_responses folder and return the specified response based on the url.
        """
        with open(TestActions.API_RESPONSES_PATH, "r") as file:
            predefined_responses = json.load(file)
            return predefined_responses.get(
                url,
                (
                    '{"message": "No predefined response found."}',
                    {"message": "No predefined response found."},
                ),
            )

    def test_vim_installed(self):
        # Test if vim is installed on the system
        result = subprocess.run(["vim", "--version"], capture_output=True)
        self.assertEqual(result.returncode, 0, "Vim is not installed on the system")

    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_user_prompt_single_newline(self, mock_input):
        # Test that screen input is captured as expected for single newline
        mock_input.return_value = "\n"
        value = Screen().input()
        assert value == "\n"

    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_user_prompt_double_newline(self, mock_input):
        # Test that screen input is captured as expected for double newline
        mock_input.return_value = "\n\n"
        value = Screen().input()
        assert value == "\n\n"

    @patch("requests.get", new=mock_requests_get)
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_process_operation_get_registry(self, mock_input):
        # Test processing the operation get_registry

        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "get_registry")
        om_parameters = OMParameterList()
        om_parameters.add_parameter(OMParameter(name="registry_id", value="registry-1"))

        # mock_input.side_effect = ['\n']
        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components
        )
        self.assertTrue(result_object.success)

        # The process_actions function should be able to extract the identifier
        found_identifier_parameter, identifier_parameter = parameter_history.get_om_parameter(
            "identifier", -1
        )
        self.assertTrue(found_identifier_parameter)
        self.assertEqual(identifier_parameter.value, "registry-1")

        # The registry-1 registry is static and should always be the same
        predefined_response = TestActions.get_predefined_responses(
            f"{TestActions.BASE_URL}/api/registries/registry-1"
        )
        self.assertEqual(
            json.loads(api_result_history[0]),
            predefined_response,
        )

        self.assertEqual(
            command,
            f'{self.RUN_MODULE_COMMAND} "get_registry" registry_id="registry-1"',
        )

    @patch("requests.get", new=mock_requests_get)
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_process_operation_choose_registry_to_store_loops(self, mock_input):
        # Test processing the operation choose_registry_to_store_loops with arguments while using and repeating loops, not using repeated

        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "choose_registry_to_store_loops")
        om_parameters = OMParameterList()
        om_parameters.add_parameter(OMParameter(name="identifier", value="registry-1"))
        skip_looping = False

        # Since we are not repeating loop 3 we are also testing if it will not prompt for the identifier
        mock_input.side_effect = [
            "y",  # [loop2End]
            "y",  # [loop2End]
            "n",  # [loop2End]
            "y",  # [loop1End]
            "y",  # [loop2End]
            "y",  # [loop2End]
            "n",  # [loop2End]
            "n",  # [loop1End]
            "n",  # [loop3End]
            "\n",  # TODO: Check What this is for
            "\n",  # [CommandPressEnter]
        ]
        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components, skip_looping
        )
        self.assertTrue(result_object.success)

        # The process_actions function should be able to extract the identifier
        found_identifier_parameter, identifier_parameter = parameter_history.get_om_parameter(
            "identifier", -1
        )
        self.assertTrue(found_identifier_parameter)
        self.assertEqual(identifier_parameter.value, "registry-1")

        found_json_string_parameter, json_string_parameter = parameter_history.get_om_parameter(
            "json_string", -1
        )
        self.assertTrue(found_json_string_parameter)

        found_file_path_parameter, file_path_parameter = parameter_history.get_om_parameter(
            "file_path", -1
        )
        self.assertTrue(found_file_path_parameter)

        # The registry-1 registry is static and should always be the same
        json_parsed_string = json.loads(json_string_parameter.value)
        mock_registry1 = TestActions.get_predefined_responses(
            f"{TestActions.BASE_URL}/api/registries/registry-1"
        )
        self.assertNotIn("message", mock_registry1)
        self.assertEqual(json_parsed_string, mock_registry1["data"])
        self.assertEqual(
            command,
            f'{self.RUN_MODULE_COMMAND} "choose_registry_to_store_loops" identifier="registry-1"',
        )

    @patch("requests.get", new=mock_requests_get)
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_process_operation_choose_registry_to_store_loops_skip_looping(self, mock_input):
        # Test processing the operation choose_registry_to_store_loops with arguments and with skip_loops active

        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "choose_registry_to_store_loops")
        om_parameters = OMParameterList()
        om_parameters.add_parameter(OMParameter(name="identifier", value="registry-1"))
        skip_looping = True

        # Since skip_looping is active, the function should not prompt for anything
        # [CommandPressEnter]
        # mock_input.side_effect = ['\n']
        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components, skip_looping
        )
        self.assertTrue(result_object.success)

        # The process_actions function should be able to extract the identifier
        # Extract parameters into a dictionary for easier access
        parameter_dict = {param.name: param for param in parameter_history}

        self.assertIn("identifier", parameter_dict)
        self.assertEqual(parameter_dict["identifier"].value, "registry-1")

        self.assertIn("json_string", parameter_dict)
        json_parsed_string = json.loads(parameter_dict["json_string"].value)
        mock_registry1 = TestActions.get_predefined_responses(
            f"{TestActions.BASE_URL}/api/registries/registry-1"
        )
        self.assertNotIn("message", mock_registry1)
        self.assertEqual(json_parsed_string, mock_registry1["data"])

        self.assertIn("file_path", parameter_dict)

        self.assertEqual(
            command,
            f'{self.RUN_MODULE_COMMAND} "choose_registry_to_store_loops" identifier="registry-1"',
        )

    @patch("requests.get", new=mock_requests_get)
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_process_operation_choose_registry_to_store_loops_repeated_change_identifier(
        self, mock_input
    ):
        # Test processing the operation choose_registry_to_store_loops with arguments and testing the repeated function and changing the identifier

        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "choose_registry_to_store_loops")
        om_parameters = OMParameterList()
        om_parameters.add_parameter(OMParameter(name="identifier", value="registry-2"))
        skip_looping = False

        # Since we are repeating loop 3 we are also testing that it will ask for the identifier and replace registry-2 with registry-1
        mock_input.side_effect = [
            "y",  # [loop2End]
            "y",  # [loop2End]
            "n",  # [loop2End]
            "y",  # [loop1End]
            "y",  # [loop2End]
            "y",  # [loop2End]
            "n",  # [loop2End]
            "n",  # [loop1End]
            "y",  # [loop3End]
            "SHOULD_NOT_WORK",  # [Input_identifier]
            "y",  # [IdentifierNotFoundRepeat]
            "registry-1",  # [Input_identifier]
            "n",  # [loop3End]
            "\n",  # [CommandPressEnter]
        ]
        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components, skip_looping
        )
        self.assertEqual(result_object.success, True)

        # The process_actions function should be able to extract the identifier
        found_identifier_parameter, identifier_parameter = parameter_history.get_om_parameter(
            "identifier", -1
        )
        self.assertTrue(found_identifier_parameter)
        self.assertEqual(identifier_parameter.value, "registry-1")

        found_json_string_parameter, json_string_parameter = parameter_history.get_om_parameter(
            "json_string", -1
        )
        self.assertTrue(found_json_string_parameter)

        found_file_path_parameter, file_path_parameter = parameter_history.get_om_parameter(
            "file_path", -1
        )
        self.assertTrue(found_file_path_parameter)

        # The registry-1 registry is static and should always be the same
        json_parsed_string = json.loads(json_string_parameter.value)
        mock_registry1 = TestActions.get_predefined_responses(
            f"{TestActions.BASE_URL}/api/registries/registry-1"
        )
        self.assertNotIn("message", mock_registry1)
        self.assertEqual(json_parsed_string, mock_registry1["data"])

        self.assertEqual(
            command,
            f'{self.RUN_MODULE_COMMAND} "choose_registry_to_store_loops" identifier="registry-1"',
        )

    @patch("requests.get", new=mock_requests_get)
    @patch("requests.post", new=mock_requests_post)
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_a_registry_from_file(self, mock_input):
        # Test processing the operation test_a_registry_from_file...

        def fetch_om_parameter_value(parameter_name, parameter_history):
            found_parameter, parameter = parameter_history.get_om_parameter(parameter_name, -1)
            if not found_parameter:
                return None
            return parameter.value

        setup_logger("om_cli")

        args = ["-l", "DEBUG"]
        collected_args = collect_arguments(args)
        update_log_level(collected_args.log_level)

        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "test_a_registry_from_file")
        om_parameters = OMParameterList()

        skip_looping = False

        mock_input.side_effect = [
            "",  # [directory_path]
            "1",  # [file_number]
            "",  # [extra_parameter]
            "registry-1",  # [filter]
            "0",  # [r_number]
            "registry-10",  # [filter]
            "10",  # [r_number]
            "\n",  # [CommandPressEnter]
        ]
        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components, skip_looping
        )
        self.assertEqual(result_object.success, True)

        auto_user = fetch_om_parameter_value("user", parameter_history)
        self.assertEqual(auto_user, pwd.getpwuid(os.getuid())[0])

        r_id = fetch_om_parameter_value("r_id", parameter_history)
        self.assertEqual(r_id, "registry-10")

        extra_parameter = fetch_om_parameter_value("extra_parameter", parameter_history)
        self.assertEqual(extra_parameter, True)
        result_file_content = fetch_om_parameter_value("result_file_content", parameter_history)
        result_file_path = fetch_om_parameter_value("result_file_path", parameter_history)

        with open(result_file_path, "r") as file:
            file_content = file.read()
            self.assertEqual(file_content, result_file_content)

        self.assertEqual(
            command,
            f'{self.RUN_MODULE_COMMAND} "test_a_registry_from_file" directory_path="{self.SCRIPT_PATH}/custom/test_resources/registries/" file_number=1 extra_parameter=True filter="registry-10" r_number=10',
        )

    @patch("requests.get", new=mock_requests_get)
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_process_operation_get_all_registries(self, mock_input):
        # Test processing the operation get_all_registries

        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "get_all_registries")
        self.assertIsNotNone(operation)
        om_parameters = OMParameterList()

        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components
        )
        self.assertTrue(result_object.success)

        # There should be at least one registry
        registries_json = json.loads(api_result_history[0])
        self.assertGreater(len(registries_json), 0)

        # The registry-1 registry should always exist
        registry_found = any(registry["id"] == "registry-1" for registry in registries_json)
        self.assertTrue(registry_found)

        self.assertEqual(command, f'{self.RUN_MODULE_COMMAND} "get_all_registries"')

    @patch("requests.get", new=mock_requests_get)
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_process_operation_get_all_registries_internal_api_mocking(self, mock_input):
        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, self.API_RESPONSES_PATH
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "get_all_registries")
        self.assertIsNotNone(operation)
        om_parameters = OMParameterList()

        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components
        )
        self.assertTrue(result_object.success)

        found_registries_json_parameter, registries_json_parameter = (
            parameter_history.get_om_parameter("registries_json", -1)
        )
        json_parsed_string = json.loads(registries_json_parameter.value)
        mock_registries = TestActions.get_predefined_responses(
            f"{TestActions.BASE_URL}/api/registries/"
        )
        self.assertNotIn("message", mock_registries)
        self.assertEqual(json_parsed_string, mock_registries)

    # TODO: Test non-stick in a loop in combination with default_value, preset_value and prompt with placeholders, use something like fetch_and_store_local_registry_files

    # TODO: Test override_parameter_name and override_output_parameter_name

    @patch("requests.get", new=mock_requests_get)
    # @patch('cli.src.action_packs.kafka_pack.produce_kafka_message', return_value=ResultObject(True, "Kafka message produced successfully", None, OMParameterList()))
    @patch("src.om_cli.services.operation_processing.Screen.input")
    def test_process_operation_send_data_to_kafka(
        self, mock_input
    ):  # , mock_produce_kafka_message):
        # Test processing the operation send_data_to_kafka to see if the right parameters are passed to the produce_kafka_message function
        # The actual Kafka instance is not used in this test

        custom_components = CustomComponents.load_custom_components(
            self.CUSTOM_PATH, self.OM_TREE_PATH, ""
        )

        om_tree = custom_components.get_om_tree()
        operation = get_operation_by_id(om_tree.operations, "send_data_to_kafka")
        om_parameters = OMParameterList()
        om_parameters.add_parameter(OMParameter(name="registry_id", value="registry-1"))

        result_object, parameter_history, api_result_history, command = process_operation(
            operation, om_parameters, custom_components
        )
        self.assertTrue(result_object.success)

        # TODO: Since the Kafka method is loaded during runtime with importlib I have not yet found a way to mock it properly
        # Relying on the result object being successful and the command being correct for now

        self.assertEqual(
            command,
            f'{self.RUN_MODULE_COMMAND} "send_data_to_kafka" registry_id="registry-1"',
        )


if __name__ == "__main__":
    unittest.main()
