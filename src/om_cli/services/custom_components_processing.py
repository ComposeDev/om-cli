# src/om_cli/services/custom_components_processing.py
import importlib.util
import inspect
import json
import os
import re
import sys
from pathlib import Path

from consolemenu import Screen

from src.om_cli.helpers.text_helpers import colorize_text
from src.om_cli.logger import logger
from src.om_cli.models.om_action import OMAction, OMActionType
from src.om_cli.models.om_condition import OMCondition
from src.om_cli.models.om_condition_group import (
    OMConditionGroup,
    OMConditionGroupOperator,
)
from src.om_cli.models.om_operation import OMOperation
from src.om_cli.models.om_parameter import OMParameter, OMParameterType
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.om_tree import OMTree

ERROR_COLOR = "red"
SCRIPT_PATH = Path(__file__).resolve().parents[3]
CUSTOM_VARIABLE_PATHS = {"WORKSPACE": SCRIPT_PATH.as_posix()}
DEFAULT_CUSTOM_PATH = f"{SCRIPT_PATH}/custom"
DEFAULT_OM_TREE_PATH = f"{SCRIPT_PATH}/custom/operation_menus/om_tree.json"
DEFAULT_MOCK_API_RESPONSES_FILE_PATH = ""


class CustomComponents:
    def __init__(
        self,
        custom_path: str,
        om_tree_path: str,
        mock_api_responses_file_path: str,
    ):
        self.custom_path = custom_path
        self.action_packs_path = os.path.join(custom_path, "action_packs")
        self.api_definitions_path = os.path.join(custom_path, "api_definitions")
        self.om_tree_path = om_tree_path
        self.mock_api_responses_file_path = mock_api_responses_file_path
        self.action_packs: dict = {}
        self.api_definitions: list = []
        self.mock_api_responses: dict = {}
        self.om_tree = None

    @staticmethod
    def load_custom_components(
        argument_custom_path: str,
        argument_om_tree_path: str,
        argument_mock_api_responses_file_path: str = "",
    ) -> "CustomComponents":
        """
        Load custom components from the custom directory.

        """
        try:
            custom_path = argument_custom_path or DEFAULT_CUSTOM_PATH
            om_tree_path = argument_om_tree_path or DEFAULT_OM_TREE_PATH
            mock_api_responses_file_path = (
                argument_mock_api_responses_file_path or DEFAULT_MOCK_API_RESPONSES_FILE_PATH
            )
            custom_components = CustomComponents(
                custom_path,
                om_tree_path,
                mock_api_responses_file_path,
            )
            if not custom_components._validate_custom_path(custom_path, om_tree_path):
                raise ValueError(f"Invalid custom path provided: {custom_path}")

            custom_components.load_action_packs(globals())
            custom_components.load_custom_api_definitions()
            custom_components.load_om_tree()
            custom_components.load_mock_api_responses()
            return custom_components
        except Exception as e:
            logger.error(f"Error while loading custom components: {e}")
            print(colorize_text(f"Error while loading custom components: {e}", ERROR_COLOR))
            Screen().input(colorize_text("\nPress enter to exit", ERROR_COLOR))
            sys.exit(1)

    def get_action_definition(self, action_pack_action_name: str):
        """
        Get the action pack function from the action packs.

        Args:
            action_pack_action_name (str): The name of the action pack action to get.

        Returns:
            dict: The action pack action definition.
        """
        return next(
            (
                action_pack[action_pack_action_name]
                for action_pack in self.action_packs.values()
                if action_pack_action_name in action_pack.keys()
            ),
            None,
        )

    def get_action_packs(self) -> dict:
        if not self.action_packs:
            self.load_action_packs(globals())
        return self.action_packs

    def get_api_definitions(self) -> list:
        if not self.api_definitions:
            self.load_custom_api_definitions()
        return self.api_definitions

    def get_api_endpoint_and_definition(self, endpoint_name: str):
        """
        Retrieves an API endpoint based on the given endpoint name.

        Args:
            endpoint_name (str): The name of the API endpoint to retrieve.

        Returns:
            dict: The API endpoint configuration.
        """
        endpoint_api_name = endpoint_name.split(".")[0]
        endpoint_name = endpoint_name.split(".")[1]

        current_api_definition = next(
            (
                api_definition
                for api_definition in self.api_definitions
                if api_definition.get("id", "") == endpoint_api_name
            ),
            None,
        )
        if not current_api_definition:
            raise ValueError(f"Unknown API {endpoint_api_name}")

        if current_api_endpoint := next(
            (
                endpoint
                for endpoint in current_api_definition.get("api_endpoints", [])
                if endpoint.get("name", "") == endpoint_name
            ),
            None,
        ):
            return current_api_definition, current_api_endpoint
        else:
            raise ValueError(f"Unknown endpoint {endpoint_name}")

    def get_mock_api_responses(self) -> dict:
        if not self.mock_api_responses:
            self.load_mock_api_responses()
        return self.mock_api_responses

    def get_argument_custom_path(self) -> str:
        return self.custom_path if self.custom_path != DEFAULT_CUSTOM_PATH else ""

    def get_argument_om_tree_file_path(self) -> str:
        return self.om_tree_path if self.om_tree_path != DEFAULT_OM_TREE_PATH else ""

    def get_argument_mock_api_responses_file_path(self) -> str:
        return (
            self.mock_api_responses_file_path
            if self.mock_api_responses_file_path != DEFAULT_MOCK_API_RESPONSES_FILE_PATH
            else ""
        )

    def get_om_tree(self) -> OMTree:
        if not self.om_tree:
            self.load_om_tree()
        if not self.om_tree:
            raise ValueError("OMTree is not loaded")
        return self.om_tree

    def load_action_packs(self, globals_object) -> None:
        """
        Load all Action pack functions from the action pack directory.
        """
        self.action_packs = self._read_and_populate_action_packs(
            self.action_packs_path, globals_object
        )

    def load_custom_api_definitions(self) -> None:
        """
        Load all custom API endpoints from the API endpoints directory.
        """
        self.api_definitions = self._read_and_populate_custom_api_definitions(
            self.api_definitions_path
        )

    def load_om_tree(self):
        """
        Load the OM tree from the OM tree file path.
        """
        self.om_tree = self._read_and_populate_om_tree(self.om_tree_path)
        self._validate_om_tree(self.om_tree)

    def load_mock_api_responses(self) -> None:
        """
        Load all mock API responses from the mock API responses directory.
        """
        self.mock_api_responses = self._read_and_populate_mock_api_responses(
            self.mock_api_responses_file_path
        )

    def _read_and_populate_action_packs(self, directory_path: str, globals_object) -> dict:
        """
        Load all Action pack functions from Python files in a directory.
        The functions are stored in a dictionary with the function name as the key and the function as the value.

        Args:
            directory (str): The directory to load the functions from.
            globals_object (dict): The globals dictionary to check for existing functions.

        Returns:
            dict: A dictionary with the function name as the key and the function as the value.
        """

        action_packs = {}

        logger.debug(f"Started loading Action packs from directory: {directory_path}")
        try:
            # List all Python files in the directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".py"):
                    logger.debug(f"Loading functions from file: {filename}")
                    module_name = filename[:-3]  # Remove the .py extension
                    module_path = os.path.join(directory_path, filename)

                    # Import the module dynamically
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if not spec or not spec.loader:
                        raise ImportError(
                            f"Failed to load module: {module_name} from path: {module_path}"
                        )

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Extract PARAMETER_DEFINITIONS from the module
                    if not hasattr(module, "PARAMETER_DEFINITIONS"):
                        raise ValueError(
                            f"PARAMETER_DEFINITIONS not found in the action pack: {module_name}"
                        )
                    action_pack_parameter_definitions = getattr(module, "PARAMETER_DEFINITIONS")
                    logger.debug(f"Loaded parameter definitions for the action pack: {module_name}")

                    actions = {}

                    # Extract functions from the module
                    for name, obj in inspect.getmembers(module, inspect.isfunction):
                        # The globals object is used to check if the function is an internal one that does not need to be loaded again
                        found_function = globals_object.get(name)
                        if found_function is None and name not in actions:
                            logger.debug(
                                f"Loaded the action pack function: {name} from the action pack: {module_name}"
                            )
                            if name.startswith("_"):
                                logger.debug(f"Skipping internal function: {name}")
                                continue
                            parameter_definitions = action_pack_parameter_definitions.get(
                                name, None
                            )
                            if parameter_definitions is None:
                                raise ValueError(
                                    f"Parameter definitions not found for action: {name}"
                                )

                            actions[name] = {
                                "parameter_definitions": parameter_definitions,
                                "function": obj,
                            }

                    action_packs[module_name] = actions
        except Exception as e:
            logger.error(f"Error while loading Action packs from directory: {directory_path}: {e}")
            raise e
        logger.debug(f"Finished loading Action packs from directory: {directory_path}")

        return action_packs

    def _read_and_populate_custom_api_definitions(self, directory_path: str) -> list:
        # load all .json files inside the custom/api_definitions folder
        configs = []

        for filename in os.listdir(directory_path):
            if filename.endswith(".json"):
                filepath = os.path.join(directory_path, filename)
                with open(filepath, "r") as file:
                    try:
                        config = json.load(file)
                        self._validate_api_definition(config)
                        logger.debug(
                            f"Loaded the API definition {config.get('name')} with the id {config.get('id')} having {len(config.get('api_endpoints'))} api endpoints"
                        )
                        configs.append(self._replace_custom_api_variables(config))
                    except Exception as e:
                        self._error_prompt_and_exit(
                            "Error while loading API endpoint from file: ", filename, e
                        )
        return configs

    def _read_and_populate_om_tree(self, om_tree_path: str) -> OMTree:
        try:
            with open(om_tree_path, "r") as file:
                om_tree_dict = json.load(file)
                om_tree = self._convert_dict_to_om_tree(om_tree_dict)
                logger.debug(f"Loaded OM tree from file: {om_tree_path}")
        except Exception as e:
            self._error_prompt_and_exit("Error while loading OM tree from file: ", om_tree_path, e)
        return om_tree

    def _read_and_populate_mock_api_responses(self, mock_responses_path: str) -> dict:
        mock_responses: dict[str, dict] = {}

        if not mock_responses_path:
            logger.debug("No mock API responses file provided.")
            return mock_responses
        try:
            with open(mock_responses_path, "r") as file:
                mock_responses = json.load(file)
                self._validate_mock_api_responses(mock_responses)
                logger.debug(
                    f"Loaded {len(mock_responses)} mock API responses from file: {mock_responses_path}"
                )
        except Exception as e:
            self._error_prompt_and_exit(
                "Error while loading mock API responses from file: ",
                mock_responses_path,
                e,
            )
        return mock_responses

    def _error_prompt_and_exit(self, error_text: str, parameter: str, e) -> None:
        logger.error(f"{error_text}{parameter}: {e}")
        Screen().input(colorize_text("\nPress enter to exit", ERROR_COLOR))
        sys.exit(1)

    def _validate_custom_path(self, custom_path: str, om_tree_path: str) -> bool:
        if not os.path.isdir(custom_path):
            logger.error("The custom path provided does not exist.")
            return False

        if not om_tree_path:
            om_tree_path = os.path.join(custom_path, "operation_menus", "om_tree.json")

        if not os.path.exists(om_tree_path):
            logger.error("The OMTree configuration file does not exist.")
            return False

        action_packs_directory = os.path.join(custom_path, "action_packs")
        if not os.path.exists(action_packs_directory):
            logger.error("The action_packs directory is missing from the custom directory.")
            return False

        api_definitions_directory = os.path.join(custom_path, "api_definitions")
        if not os.path.exists(api_definitions_directory):
            logger.error("The api_definitions_directory is missing from the custom directory.")
            return False
        return True

    def _validate_api_definition(self, config: dict) -> None:
        if not isinstance(config, dict):
            raise ValueError("API definition must be a dictionary")
        if not config.get("name"):
            raise ValueError("API definition name is required")
        if not isinstance(config.get("name"), str):
            raise ValueError("API definition name must be a string")
        if not config.get("id"):
            raise ValueError("API definition id is required")
        if not isinstance(config.get("id"), str):
            raise ValueError("API definition id must be a string")
        if not config.get("request_timeout"):
            raise ValueError("API definition request_timeout is required")
        if not isinstance(config.get("request_timeout"), int):
            raise ValueError("API definition request_timeout must be an integer")
        if not config.get("description"):
            raise ValueError("API definition description is required")
        if not isinstance(config.get("description"), str):
            raise ValueError("API definition description must be a string")
        if not isinstance(config.get("custom_variables"), dict):
            raise ValueError("API definition custom_variables must be a dictionary")
        if not config["custom_variables"].get("BASE_URL"):
            raise ValueError("API definition custom_variables must have a BASE_URL")
        if not isinstance(config.get("api_endpoints"), list):
            raise ValueError("The api_endpoints property must be a list")
        api_endpoints = config.get("api_endpoints", [])
        for endpoint in api_endpoints:
            self._validate_api_endpoints(endpoint)

    def _validate_api_endpoints(self, endpoint: dict) -> None:
        if not isinstance(endpoint, dict):
            raise ValueError("Each endpoint must be a dictionary")
        if "name" not in endpoint:
            raise ValueError("Each endpoint must have a name")
        if not isinstance(endpoint.get("name"), str):
            raise ValueError("Each endpoint name must be a string")
        if "request_type" not in endpoint:
            raise ValueError("Each endpoint must have a request_type")
        if not isinstance(endpoint.get("request_type"), str):
            raise ValueError("Each endpoint request_type must be a string")
        if "url" not in endpoint:
            raise ValueError("Each endpoint must have a url")
        if not isinstance(endpoint.get("url"), str):
            raise ValueError("Each endpoint url must be a string")
        if "headers" not in endpoint:
            raise ValueError("Each endpoint must have headers")
        if not isinstance(endpoint.get("headers"), dict):
            raise ValueError("Each endpoint headers must be a dict")
        if "data" not in endpoint:
            raise ValueError("Each endpoint must have data")
        if endpoint.get("data") and not isinstance(endpoint.get("data"), str):
            raise ValueError("Each endpoint data must be a string or null")
        if "params" not in endpoint:
            raise ValueError("Each endpoint must have params")
        if endpoint.get("params") and not isinstance(endpoint.get("params"), str):
            raise ValueError("Each endpoint params must be a string or null")
        if "response_variables" not in endpoint:
            raise ValueError("Each endpoint must have response_variables")
        if endpoint.get("response_variables") and not isinstance(
            endpoint.get("response_variables"), dict
        ):
            raise ValueError("Each endpoint response_variables must be a dict or null")

        # TODO: Add validation of response_variables

    def _validate_om_tree(self, om_tree: OMTree) -> None:
        """
        Validates the OMTree object against the Action pack actions and API definitions.

        Args:
            om_tree (OMTree): The OMTree object to validate.

        Raises:
            ValueError: If the OMTree is invalid.
        """

        def validate_parameter(param: OMParameter, action_pack_action: dict):
            if param.custom_parameter:
                logger.debug(f"Skipping validation for custom parameter: {param.name}")
                return

            param_name = param.name
            param_name_text = param_name

            if param.override_parameter_name:
                param_name = param.override_parameter_name
                param_name_text = f"{param_name} (overridden from {param_name_text})"

            parameter_definition = action_pack_action["parameter_definitions"].get(param_name)
            if not parameter_definition:
                raise ValueError(
                    f"No parameter definition found for the parameter: '{param_name_text}'"
                )

            if parameter_definition.get("type") != param.type.name:
                raise ValueError(
                    f"Parameter type mismatch for parameter: '{param_name_text}'. Expected: '{parameter_definition.get('type')}', Found: '{param.type.name}'"
                )

        def validate_action(action: OMAction, operation: OMOperation):
            if action.type == OMActionType.API_REQUEST:
                # TODO: Add API request parameter validation
                api_definition, api_endpoint = self.get_api_endpoint_and_definition(action.name)
                if not api_endpoint:
                    raise ValueError(f"No API endpoint named: '{action.name}'")

            elif action.type == OMActionType.FUNCTION_CALL:
                # TODO: Add listing used and unused parameters
                action_pack_action = self.get_action_definition(action.name)
                if not action_pack_action:
                    raise ValueError(f"No loaded Action pack action named: '{action.name}'")

                for param in action.parameters:
                    validate_parameter(param, action_pack_action)

        def validate_operation(operation: OMOperation):
            for action in operation.actions:
                try:
                    validate_action(action, operation)
                except Exception as e:
                    raise ValueError(
                        f"Invalid OMTree configuration found in the action '{action.name}' from the operation '{operation.operation_id}': {e}"
                    )
            if operation.children:
                for child in operation.children:
                    validate_operation(child)

        for operation in om_tree.operations:
            validate_operation(operation)

    def _validate_mock_api_responses(self, config: dict) -> None:
        if not isinstance(config, dict):
            raise ValueError("Mock API responses must be a dictionary")
        for k, v in config.items():
            if not isinstance(k, str):
                raise ValueError("Each response key must be a string")

            # Check if the value is a valid list or dictionary or json string
            if not isinstance(v, (list, dict, str)):
                raise ValueError("Each response value must be a list, dictionary, or JSON string")

    def _convert_dict_to_om_tree(self, om_tree_dict: dict) -> OMTree:
        """
        Converts the dictionary representation of an operation tree into an OMTree object.

        Args:
            om_tree_dict (dict): The dictionary representation of the operation tree.

        Returns:
            OMTree: The OMTree object.
        """
        custom_variables = om_tree_dict.get("custom_variables", {})
        return OMTree(
            name=om_tree_dict["name"],
            description=om_tree_dict["description"],
            custom_variables=custom_variables,
            operations=[
                self._dict_to_om_operation(op, custom_variables)
                for op in om_tree_dict["operations"]
            ],
        )

    def _dict_to_om_operation(self, operation_dict: dict, custom_variables: dict) -> OMOperation:
        """
        Converts the dictionary representation of an operation into an OMOperation object.
        Replaces custom variables in the operation attributes.

        Args:
            operation_dict (dict): The dictionary representation of the operation.
            custom_variables (dict): The dictionary of custom variables.

        Returns:
            OMOperation: The OMOperation object.
        """
        return OMOperation(
            operation_id=self._replace_custom_tree_variables(
                operation_dict["operation_id"], custom_variables
            ),
            menu_title=self._replace_custom_tree_variables(
                operation_dict["menu_title"], custom_variables
            ),
            help_text=self._replace_custom_tree_variables(
                operation_dict["help_text"], custom_variables
            ),
            actions=(
                [
                    self._dict_to_om_action(action, custom_variables)
                    for action in operation_dict.get("actions", [])
                ]
                if operation_dict.get("actions") is not None
                else []
            ),
            children=(
                [
                    self._dict_to_om_operation(child, custom_variables)
                    for child in operation_dict.get("children", [])
                ]
                if operation_dict.get("children") is not None
                else []
            ),
        )

    def _dict_to_om_action(self, action_dict: dict, custom_variables: dict) -> OMAction:
        """
        Converts the dictionary representation of an action into an OMAction object.
        Replaces custom variables in the action attributes.

        Args:
            action_dict (dict): The dictionary representation of the action.
            custom_variables (dict): The dictionary of custom variables.

        Returns:
            OMAction: The OMAction object
        """
        parameters = OMParameterList()
        if action_dict.get("parameters"):
            for param in action_dict["parameters"]:
                parameters.add_parameter(self._dict_to_om_parameter(param, custom_variables))

        return OMAction(
            type=OMActionType[action_dict["type"]],
            name=self._replace_custom_tree_variables(action_dict["name"], custom_variables),
            loop_number=action_dict.get("loop_number"),
            custom_loop_repeat_prompt=self._replace_custom_tree_variables(
                action_dict.get("custom_loop_repeat_prompt"), custom_variables
            ),
            failure_termination=action_dict.get("failure_termination", True),
            parameters=parameters,
            skip_if_conditions=(
                [
                    self._dict_to_om_condition_group(cond_group, custom_variables)
                    for cond_group in action_dict.get("skip_if_conditions", [])
                ]
                if action_dict.get("skip_if_conditions") is not None
                else []
            ),
        )

    def _dict_to_om_parameter(self, param_dict: dict, custom_variables: dict) -> OMParameter:
        """
        Converts the dictionary representation of a parameter into an OMParameter object.
        Replaces custom variables in the parameter attributes.

        Args:
            param_dict (dict): The dictionary representation of the parameter.
            custom_variables (dict): The dictionary of custom variables.

        Returns:
            OMParameter: The OMParameter object.
        """
        return OMParameter(
            name=self._replace_custom_tree_variables(param_dict["name"], custom_variables),
            type=(
                OMParameterType[param_dict["type"]]
                if param_dict.get("type")
                else OMParameterType.STRING
            ),
            default_value=self._replace_custom_tree_variables(
                param_dict.get("default_value"), custom_variables
            ),
            custom_text=self._replace_custom_tree_variables(
                param_dict.get("custom_text"), custom_variables
            ),
            api_parameter_name=self._replace_custom_tree_variables(
                param_dict.get("api_parameter_name"), custom_variables
            ),
            non_stick=param_dict.get("non_stick", False),
            preset_value=self._replace_custom_tree_variables(
                param_dict.get("preset_value"), custom_variables
            ),
            custom_input_name=self._replace_custom_tree_variables(
                param_dict.get("custom_input_name"), custom_variables
            ),
            command_parameter=param_dict.get("command_parameter", False),
            custom_parameter=param_dict.get("custom_parameter", False),
            override_output_parameter_name=param_dict.get("override_output_parameter_name", False),
            override_parameter_name=self._replace_custom_tree_variables(
                param_dict.get("override_parameter_name"), custom_variables
            ),
        )

    def _dict_to_om_condition(self, condition_dict: dict, custom_variables: dict) -> OMCondition:
        """
        Converts the dictionary representation of a condition into an OMCondition object.
        Replaces custom variables in the condition attributes.

        Args:
            condition_dict (dict): The dictionary representation of the condition.
            custom_variables (dict): The dictionary of custom variables.

        Returns:
            OMCondition: The OMCondition object.
        """
        return OMCondition(
            parameter_name=self._replace_custom_tree_variables(
                condition_dict["parameter_name"], custom_variables
            ),
            jsonpath=self._replace_custom_tree_variables(
                condition_dict["jsonpath"], custom_variables
            ),
            regex=self._replace_custom_tree_variables(condition_dict["regex"], custom_variables),
            skip_if_path_not_found=condition_dict.get("skip_if_path_not_found"),
        )

    def _dict_to_om_condition_group(
        self, condition_group_dict: dict, custom_variables: dict
    ) -> OMConditionGroup:
        """
        Converts the dictionary representation of a condition group into an OMConditionGroup object.
        Replaces custom variables in the condition group attributes.

        Args:
            condition_group_dict (dict): The dictionary representation of the condition group.
            custom_variables (dict): The dictionary of custom variables.

        Returns:
            OMConditionGroup: The OMConditionGroup object.
        """
        return OMConditionGroup(
            conditions=(
                [
                    self._dict_to_om_condition(cond, custom_variables)
                    for cond in condition_group_dict["conditions"]
                ]
                if condition_group_dict.get("conditions")
                else []
            ),
            operator=(
                OMConditionGroupOperator[condition_group_dict["operator"]]
                if condition_group_dict.get("operator")
                else OMConditionGroupOperator.AND
            ),
        )

    def _replace_custom_tree_variables(self, value, custom_variables) -> str:
        """
        Replaces placeholders in the format {{{XXX}}} with the corresponding value from custom_variables and possibly CUSTOM_PATHS.

        Args:
            value (str): The string value to process.
            custom_variables (dict): The dictionary of custom variables.

        Returns:
            str: The processed string with placeholders replaced.
        """
        if isinstance(value, str):
            for key, var_value in custom_variables.items():
                placeholder = f"{{{{{{{key}}}}}}}"
                if placeholder in value:
                    # If the var_value contains a $XXX placeholder, check for and replace it with a corresponding value from the CUSTOM_PATHS before expanding the vars
                    if "$" in var_value:
                        var_value = re.sub(
                            r"\$(\w+)",
                            lambda m: CUSTOM_VARIABLE_PATHS.get(m.group(1), m.group(0)),
                            var_value,
                        )

                    value = value.replace(placeholder, os.path.expandvars(var_value))
        return value

    def _replace_custom_api_variables(self, config: dict) -> dict:
        env_vars = config.get("custom_variables", {})
        pattern = re.compile(r"\{\{(\w+)\}\}")

        def replace(match):
            var_name = match.group(1)
            return env_vars.get(var_name, match.group(0))

        def recursive_replace(item):
            if isinstance(item, dict):
                return {k: recursive_replace(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [recursive_replace(i) for i in item]
            elif isinstance(item, str):
                return pattern.sub(replace, item)
            else:
                return item

        return recursive_replace(config)
