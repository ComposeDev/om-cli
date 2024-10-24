# src/om_cli/services/operation_tree_generator.py

import ast
import json
import os
import re
import sys
from typing import Any

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

"""
Default values for the operation tree objects
Used to filter out default values when converting objects to dictionaries
To avoid unnecessary key-value pairs in the dictionary and improve readability
"""
DEFAULT_VALUES: dict = {
    "OMTree": {
        # 'name': '',
        # 'description': '',
        "custom_variables": None,
        # 'operations': []
    },
    "OMOperation": {
        # 'operation_id': '',
        # 'menu_title': '',
        "help_text": "This is a sample help text",
        "actions": [],
        "children": [],
    },
    "OMAction": {
        # 'type': None,
        # 'name': '',
        "loop_number": None,
        "custom_loop_repeat_prompt": None,
        "failure_termination": True,
        "parameters": [],
        "skip_if_conditions": [],
    },
    "OMParameter": {
        # 'name': '',
        "type": "STRING",
        "default_value": None,
        "custom_text": None,
        "api_parameter_name": None,
        "non_stick": False,
        "preset_value": None,
        "custom_input_name": None,
        "command_parameter": False,
        "custom_parameter": False,
        "override_output_parameter_name": False,
        "override_parameter_name": None,
    },
    "OMCondition": {
        # 'parameter_name': '',
        # 'jsonpath': '',
        # 'regex': '',
        "skip_if_path_not_found": None
    },
    "OMConditionGroup": {
        # 'conditions': None,
        "operator": "AND"
    },
}


def load_om_tree_from_json_file(file_path: str) -> OMTree:
    """
    Loads the OMTree object from a file.

    Args:
        file_path (str): The path to the input file.

    Returns:
        OMTree: The OMTree object.
    """
    logger.debug("Starting to load the OMTree from JSON file...")

    try:
        with open(file_path, "r") as file:
            om_tree_json = json.load(file)
    except Exception as e:
        log_error_and_await_prompt("Failed to load the menu config file: %s", e)

    try:
        om_tree = dict_to_om_tree(om_tree_json)
    except Exception as e:
        log_error_and_await_prompt("Failed to convert the menu config file to an OMTree: %s", e)
    logger.debug("Finished loading the OMTree from file.")

    return om_tree


def log_error_and_await_prompt(arg0, e):
    logger.error(arg0, e)
    Screen().input(colorize_text("\nPress enter to exit", "red"))
    sys.exit(1)


def load_om_tree_from_dict_file_and_convert_to_json(file_path: str) -> OMTree:
    """
    Loads the OMTree object from a file.
    Also converts the OMTree object to a JSON-compliant string and writes it to a file.
    Then reads the JSON-compliant string from the file and loads it back into an OMTree object.
    Validates that the original operation tree and the converted operation tree are identical.

    Args:
        file_path (str): The path to the input file.

    Returns:
        OMTree: The OMTree object.
    """
    logger.debug("Starting to load the OMTree from file...")

    read_om_tree_dict = read_json_from_file(file_path)
    json_tree = format_dict_json_compliant(read_om_tree_dict)
    # Store the formatted JSON-compliant string in a file for debugging purposes using native Python JSON module write
    with open("om_tree.json", "w") as file:
        file.write(json_tree)

    # Read the json file and load the OMTree object
    with open("om_tree.json", "r") as file:
        om_tree_json = json.load(file)

    om_tree = dict_to_om_tree(read_om_tree_dict)
    om_tree_json = dict_to_om_tree(om_tree_json)

    success, message = validate_om_tree(om_tree, om_tree_json)

    if not success:
        logger.error(
            "The original operation tree and the converted operation tree are not identical:\n%s",
            message,
        )
        sys.exit(1)
    else:
        logger.info("The original operation tree and the converted operation tree are identical.")

    logger.debug("Finished loading the OMTree from file.")

    return om_tree


def generate_json_config_from_operation_tree(om_tree: OMTree, output_file: str) -> OMTree:
    """
    Generates a json file representation of the configuration from an om_tree.
    Used to do large changes to the configuration and then save it to a new file.

    Args:
        om_tree (OMTree): The OMTree object.
        output_file (str): The path to the output file.

    Returns:
        OMTree: The OMTree object generated from the dictionary.

    Raises:
        Exception: If the original operation tree and the converted operation tree are not identical.
    """
    logger.debug("Starting to generate a new om_tree configuration from te current om_tree...")

    om_tree_dict = om_tree_to_dict(om_tree)

    om_tree_operations_customized = replace_with_custom_variables(
        om_tree_dict.get("operations"), om_tree_dict.get("custom_variables")
    )
    om_tree_dict["operations"] = om_tree_operations_customized
    formatted_om_tree = format_dict_json_compliant(om_tree_dict)
    write_config_to_file(formatted_om_tree, output_file)

    read_om_tree_dict = read_json_from_file(output_file)
    new_om_tree = dict_to_om_tree(read_om_tree_dict)

    success, message = validate_om_tree(om_tree, new_om_tree)

    if not success:
        logger.error(
            "The original operation tree and the converted operation tree are not identical:\n%s",
            message,
        )
        sys.exit(1)
    else:
        logger.info("The original operation tree and the converted operation tree are identical.")

    logger.debug("Finished generating dictionary from the operation tree.")

    return new_om_tree


""" Generate dictionary from OMTree Start """


def replace_with_custom_variables(value: Any, custom_variables: dict[str, Any]) -> Any:
    """
    Recursively replaces parts of string values with custom variable placeholders.

    Args:
        value (Any): The value to check and replace.
        custom_variables (dict[str, Any]): The custom variables dictionary.

    Returns:
        Any: The value with custom variable placeholders replaced.
    """
    if isinstance(value, str):
        for var_name, var_value in custom_variables.items():
            # Expand environment variables in the custom variable value
            var_value_str = str(os.path.expandvars(var_value))
            value = re.sub(re.escape(var_value_str), f"{{{{{{{var_name}}}}}}}", value)
        return value
    elif isinstance(value, dict):
        return {k: replace_with_custom_variables(v, custom_variables) for k, v in value.items()}
    elif isinstance(value, list):
        return [replace_with_custom_variables(item, custom_variables) for item in value]
    else:
        return value


def om_tree_to_dict(tree: OMTree) -> dict:
    """
    Converts the operation tree into a dictionary representation of the operation tree.

    Args:
        tree (OMTree): The operation tree to convert.

    Returns:
        dict: The dictionary representation of the operation tree.
    """
    tree_dict: dict[str, Any] = {
        "name": str(tree.name),
        "description": str(tree.description),
        "custom_variables": tree.custom_variables,
        "operations": [om_operation_to_dict(operation) for operation in tree.operations],
    }
    return {
        k: v for k, v in tree_dict.items() if v is not None and v != DEFAULT_VALUES["OMTree"].get(k)
    }


def om_operation_to_dict(operation: OMOperation) -> dict:
    """
    Converts the operation into a dictionary representation of the operation.

    Args:
        operation (OMOperation): The operation to convert.

    Returns:
        dict: The dictionary representation of the operation.
    """
    operation_dict: dict[str, Any] = {
        "operation_id": str(operation.operation_id),
        "menu_title": str(operation.menu_title),
        "help_text": str(operation.help_text),
        "actions": (
            [om_action_to_dict(action) for action in operation.actions]
            if operation.actions is not None
            else None
        ),
        "children": (
            [om_operation_to_dict(child) for child in operation.children]
            if operation.children is not None
            else None
        ),
    }
    return {
        k: v
        for k, v in operation_dict.items()
        if v is not None and v != DEFAULT_VALUES["OMOperation"].get(k)
    }


def om_action_to_dict(action: OMAction) -> dict:
    """
    Converts the action into a dictionary representation of the action.

    Args:
        action (OMAction): The action to convert.

    Returns:
        dict: The dictionary representation of the action.
    """
    action_dict: dict[str, Any] = {
        "type": str(action.type.name),
        "name": str(action.name),
    }
    if action.loop_number is not None:
        action_dict["loop_number"] = str(action.loop_number)
    if action.custom_loop_repeat_prompt is not None:
        action_dict["custom_loop_repeat_prompt"] = str(action.custom_loop_repeat_prompt)
    if action.failure_termination is not None:
        action_dict["failure_termination"] = action.failure_termination
    action_dict["parameters"] = (
        [om_parameter_to_dict(param) for param in action.parameters]
        if action.parameters.has_items()
        else None
    )
    action_dict["skip_if_conditions"] = (
        [om_condition_group_to_dict(cond_group) for cond_group in action.skip_if_conditions]
        if action.skip_if_conditions is not None
        else None
    )
    return {
        k: v
        for k, v in action_dict.items()
        if v is not None and v != DEFAULT_VALUES["OMAction"].get(k)
    }


def om_parameter_to_dict(parameter: OMParameter) -> dict:
    """
    Converts the parameter into a dictionary representation of the parameter.

    Args:
        parameter (OMParameter): The parameter to convert.

    Returns:
        dict: The dictionary representation of the parameter.
    """
    param_dict: dict[str, Any] = {
        "name": str(parameter.name),
        "type": str(parameter.type.name),
    }
    if parameter.custom_input_name is not None:
        param_dict["custom_input_name"] = str(parameter.custom_input_name)
    if parameter.api_parameter_name is not None:
        param_dict["api_parameter_name"] = str(parameter.api_parameter_name)
    if parameter.override_parameter_name is not None:
        param_dict["override_parameter_name"] = str(parameter.override_parameter_name)
    if parameter.default_value is not None:
        param_dict["default_value"] = str(parameter.default_value)
    if parameter.custom_text is not None:
        param_dict["custom_text"] = str(parameter.custom_text)
    if parameter.preset_value is not None:
        param_dict["preset_value"] = str(parameter.preset_value)
    if parameter.command_parameter is not None:
        param_dict["command_parameter"] = parameter.command_parameter
    if parameter.non_stick is not None:
        param_dict["non_stick"] = parameter.non_stick
    if parameter.custom_parameter is not None:
        param_dict["custom_parameter"] = parameter.custom_parameter
    if parameter.override_output_parameter_name is not None:
        param_dict["override_output_parameter_name"] = parameter.override_output_parameter_name
    return {
        k: v
        for k, v in param_dict.items()
        if v is not None and v != DEFAULT_VALUES["OMParameter"].get(k)
    }


def om_condition_to_dict(condition: OMCondition) -> dict:
    """
    Converts the condition into a dictionary representation of the condition.

    Args:
        condition (OMCondition): The condition to convert.

    Returns:
        dict: The dictionary representation of the condition.
    """
    condition_dict: dict[str, Any] = {
        "parameter_name": str(condition.parameter_name),
        "jsonpath": str(condition.jsonpath),
        "regex": str(condition.regex),
    }
    if condition.skip_if_path_not_found is not None:
        condition_dict["skip_if_path_not_found"] = condition.skip_if_path_not_found
    return {
        k: v
        for k, v in condition_dict.items()
        if v is not None and v != DEFAULT_VALUES["OMCondition"].get(k)
    }


def om_condition_group_to_dict(condition_group: OMConditionGroup) -> dict:
    """
    Converts the condition group into a dictionary representation of the condition group.

    Args:
        condition_group (OMConditionGroup): The condition group to convert.

    Returns:
        dict: The dictionary representation of the condition group.
    """
    condition_group_dict: dict[str, Any] = {
        "conditions": [om_condition_to_dict(cond) for cond in condition_group.conditions]
    }
    if condition_group.operator is not None:
        condition_group_dict["operator"] = str(condition_group.operator.name)
    return {
        k: v
        for k, v in condition_group_dict.items()
        if v is not None and v != DEFAULT_VALUES["OMConditionGroup"].get(k)
    }


""" Generate dictionary from operation tree End """
""" Miscellaneous functions Start """


def replace_custom_variables(value, custom_variables) -> str:
    """
    Replaces placeholders in the format {{{XXX}}} with the corresponding value from custom_variables.

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
                value = value.replace(placeholder, os.path.expandvars(var_value))
    return value


def escape_string(s: str) -> str:
    """
    Escape special characters in a string for JSON compliance.

    Args:
        s (str): The string to escape.

    Returns:
        str: The escaped string.
    """
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def format_dict_json_compliant(data, indent: int = 0) -> str:
    """
    Format a dictionary into a JSON-compliant string with compact representation.

    Args:
        data (dict): The dictionary to format.
        indent (int): The current indentation level.

    Returns:
        str: The formatted JSON-compliant string.
    """
    formatted_str = ""
    indent_str = " " * (indent * 4)
    if isinstance(data, dict):
        formatted_str += "{ "
        for key, value in data.items():
            if value is None:
                continue
            key = escape_string(key)
            if isinstance(value, list):
                formatted_str += f'"{key}": [\n'
                for item in value:
                    formatted_str += (
                        f"{indent_str}    {format_dict_json_compliant(item, indent + 1)},\n"
                    )
                formatted_str = formatted_str.rstrip(",\n") + f"\n{indent_str}], "
            else:
                formatted_str += f'"{key}": {format_dict_json_compliant(value, indent + 1)}, '
        formatted_str = formatted_str.rstrip(", ") + " }"
    elif isinstance(data, list):
        formatted_str += "[ "
        for item in data:
            formatted_str += f"{format_dict_json_compliant(item, indent + 1)}, "
        formatted_str = formatted_str.rstrip(", ") + " ]"
    elif isinstance(data, str):
        formatted_str += f'"{escape_string(data)}"'
    elif isinstance(data, bool):
        formatted_str += "true" if data else "false"
    elif isinstance(data, (int, float)):
        formatted_str += str(data)
    else:
        formatted_str += f'"{escape_string(str(data))}"'
    return formatted_str


def write_config_to_file(data, output_file: str):
    """
    Writes the formatted configuration to a file.

    Args:
        data (dict): The configuration to write.
        output_file (str): The path to the output file.
    """
    with open(output_file, "w") as file:
        file.write(data)


def read_dict_from_file(input_file: str) -> dict:
    """
    Reads the formatted dictionary from a file and parses it back into a dictionary.

    Args:
        input_file (str): The path to the input file.

    Returns:
        dict: The parsed dictionary.
    """
    with open(input_file, "r") as file:
        data = file.read()
    return ast.literal_eval(data)


def read_json_from_file(input_file: str) -> dict:
    """
    Reads the JSON-compliant string from a file and parses it back into a dictionary.

    Args:
        input_file (str): The path to the input file.

    Returns:
        dict: The parsed dictionary.
    """
    with open(input_file, "r") as file:
        data = json.load(file)
    return data


""" Miscellaneous functions End """
""" Generate OMTree from dictionary Start """


def dict_to_om_tree(tree_dict: dict) -> OMTree:
    """
    Converts the dictionary representation of an operation tree into an OMTree object.

    Args:
        tree_dict (dict): The dictionary representation of the operation tree.

    Returns:
        OMTree: The OMTree object.
    """
    custom_variables = tree_dict.get("custom_variables", {})
    return OMTree(
        name=tree_dict["name"],
        description=tree_dict["description"],
        custom_variables=custom_variables,
        operations=[dict_to_om_operation(op, custom_variables) for op in tree_dict["operations"]],
    )


def dict_to_om_operation(operation_dict: dict, custom_variables: dict) -> OMOperation:
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
        operation_id=replace_custom_variables(operation_dict["operation_id"], custom_variables),
        menu_title=replace_custom_variables(operation_dict["menu_title"], custom_variables),
        help_text=replace_custom_variables(operation_dict["help_text"], custom_variables),
        actions=(
            [
                dict_to_om_action(action, custom_variables)
                for action in operation_dict.get("actions", [])
            ]
            if operation_dict.get("actions") is not None
            else []
        ),
        children=(
            [
                dict_to_om_operation(child, custom_variables)
                for child in operation_dict.get("children", [])
            ]
            if operation_dict.get("children") is not None
            else []
        ),
    )


def dict_to_om_action(action_dict: dict, custom_variables: dict) -> OMAction:
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
            parameters.add_parameter(dict_to_om_parameter(param, custom_variables))

    return OMAction(
        type=OMActionType[action_dict["type"]],
        name=replace_custom_variables(action_dict["name"], custom_variables),
        loop_number=action_dict.get("loop_number"),
        custom_loop_repeat_prompt=replace_custom_variables(
            action_dict.get("custom_loop_repeat_prompt"), custom_variables
        ),
        failure_termination=action_dict.get("failure_termination", True),
        parameters=parameters,
        skip_if_conditions=(
            [
                dict_to_om_condition_group(cond_group, custom_variables)
                for cond_group in action_dict.get("skip_if_conditions", [])
            ]
            if action_dict.get("skip_if_conditions") is not None
            else []
        ),
    )


def dict_to_om_parameter(param_dict: dict, custom_variables: dict) -> OMParameter:
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
        name=replace_custom_variables(param_dict["name"], custom_variables),
        type=(
            OMParameterType[param_dict["type"]]
            if param_dict.get("type")
            else OMParameterType.STRING
        ),
        default_value=replace_custom_variables(param_dict.get("default_value"), custom_variables),
        custom_text=replace_custom_variables(param_dict.get("custom_text"), custom_variables),
        api_parameter_name=replace_custom_variables(
            param_dict.get("api_parameter_name"), custom_variables
        ),
        non_stick=param_dict.get("non_stick", False),
        preset_value=replace_custom_variables(param_dict.get("preset_value"), custom_variables),
        custom_input_name=replace_custom_variables(
            param_dict.get("custom_input_name"), custom_variables
        ),
        command_parameter=param_dict.get("command_parameter", False),
        custom_parameter=param_dict.get("custom_parameter", False),
        override_output_parameter_name=param_dict.get("override_output_parameter_name", False),
        override_parameter_name=replace_custom_variables(
            param_dict.get("override_parameter_name"), custom_variables
        ),
    )


def dict_to_om_condition(condition_dict: dict, custom_variables: dict) -> OMCondition:
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
        parameter_name=replace_custom_variables(condition_dict["parameter_name"], custom_variables),
        jsonpath=replace_custom_variables(condition_dict["jsonpath"], custom_variables),
        regex=replace_custom_variables(condition_dict["regex"], custom_variables),
        skip_if_path_not_found=condition_dict.get("skip_if_path_not_found"),
    )


def dict_to_om_condition_group(
    condition_group_dict: dict, custom_variables: dict
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
                dict_to_om_condition(cond, custom_variables)
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


""" Generate OMTree from dictionary End """
""" Validate OMTree Start """


def validate_om_tree(original_tree: OMTree, converted_tree: OMTree) -> tuple[bool, str]:
    """
    Validates that the original operation tree and the converted operation tree are identical.

    Args:
        original_tree (OMTree): The original operation tree.
        converted_tree (OMTree): The converted operation tree.

    Returns:
        tuple: (bool, str) True if the trees are identical, False otherwise, with a message.
    """
    if original_tree.name != converted_tree.name:
        return (
            False,
            f"Tree name mismatch: {original_tree.name} != {converted_tree.name}",
        )
    if original_tree.description != converted_tree.description:
        return (
            False,
            f"Tree description mismatch: {original_tree.description} != {converted_tree.description}",
        )
    if original_tree.custom_variables != converted_tree.custom_variables:
        return (
            False,
            f"Tree custom variables mismatch: {original_tree.custom_variables} != {converted_tree.custom_variables}",
        )
    result, message = validate_lists(
        original_tree.operations, converted_tree.operations, validate_operations
    )
    if not result:
        return False, f"Tree operations mismatch: {message}"

    return True, "Trees are identical"


def validate_operations(original_op: OMOperation, converted_op: OMOperation) -> tuple[bool, str]:
    """
    Validates that the original and converted operations are identical.

    Args:
        original_op (OMOperation): The original operation.
        converted_op (OMOperation): The converted operation.

    Returns:
        tuple: (bool, str) True if the operations are identical, False otherwise, with a message.
    """
    if original_op.operation_id != converted_op.operation_id:
        return (
            False,
            f"Operation ID mismatch: {original_op.operation_id} != {converted_op.operation_id}",
        )
    if original_op.menu_title != converted_op.menu_title:
        return (
            False,
            f"Operation menu title mismatch: {original_op.menu_title} != {converted_op.menu_title}",
        )
    if original_op.help_text != converted_op.help_text:
        return (
            False,
            f"Operation help text mismatch: {original_op.help_text} != {converted_op.help_text}",
        )
    result, message = validate_lists(original_op.actions, converted_op.actions, validate_actions)
    if not result:
        return False, f"Operation actions mismatch: {message}"
    result, message = validate_lists(
        original_op.children, converted_op.children, validate_operations
    )
    if not result:
        return False, f"Operation children mismatch: {message}"

    return True, "Operations are identical"


def validate_actions(original_action: OMAction, converted_action: OMAction) -> tuple[bool, str]:
    """
    Validates that the original and converted actions are identical.

    Args:
        original_action (OMAction): The original action.
        converted_action (OMAction): The converted action.

    Returns:
        tuple: (bool, str) True if the actions are identical, False otherwise, with a message.
    """
    if original_action.type != converted_action.type:
        return (
            False,
            f"Action type mismatch: {original_action.type} != {converted_action.type}",
        )
    if original_action.name != converted_action.name:
        return (
            False,
            f"Action name mismatch: {original_action.name} != {converted_action.name}",
        )
    if original_action.loop_number != converted_action.loop_number:
        return (
            False,
            f"Action loop number mismatch: {original_action.loop_number} != {converted_action.loop_number}",
        )
    if original_action.custom_loop_repeat_prompt != converted_action.custom_loop_repeat_prompt:
        return (
            False,
            f"Action custom loop repeat prompt mismatch: {original_action.custom_loop_repeat_prompt} != {converted_action.custom_loop_repeat_prompt}",
        )
    if original_action.failure_termination != converted_action.failure_termination:
        return (
            False,
            f"Action failure termination mismatch: {original_action.failure_termination} != {converted_action.failure_termination}",
        )
    result, message = validate_om_parameter_list(
        original_action.parameters, converted_action.parameters, validate_parameters
    )
    if not result:
        return False, f"Action parameters mismatch: {message}"
    result, message = validate_lists(
        original_action.skip_if_conditions,
        converted_action.skip_if_conditions,
        validate_condition_groups,
    )
    if not result:
        return False, f"Action skip if conditions mismatch: {message}"

    return True, "Actions are identical"


def validate_parameters(
    original_param: OMParameter, converted_param: OMParameter
) -> tuple[bool, str]:
    """
    Validates that the original and converted parameters are identical.

    Args:
        original_param (OMParameter): The original parameter.
        converted_param (OMParameter): The converted parameter.

    Returns:
        tuple: (bool, str) True if the parameters are identical, False otherwise, with a message.
    """
    if original_param.name != converted_param.name:
        return (
            False,
            f"Parameter name mismatch: {original_param.name} != {converted_param.name}",
        )
    if original_param.type != converted_param.type:
        return (
            False,
            f"Parameter type mismatch: {original_param.type} != {converted_param.type}",
        )
    if original_param.default_value != converted_param.default_value:
        return (
            False,
            f"Parameter default value mismatch: {original_param.default_value} != {converted_param.default_value}",
        )
    if original_param.custom_text != converted_param.custom_text:
        return (
            False,
            f"Parameter custom text mismatch: {original_param.custom_text} != {converted_param.custom_text}",
        )
    if original_param.api_parameter_name != converted_param.api_parameter_name:
        return (
            False,
            f"Parameter API parameter name mismatch: {original_param.api_parameter_name} != {converted_param.api_parameter_name}",
        )
    if original_param.non_stick != converted_param.non_stick:
        return (
            False,
            f"Parameter non-stick mismatch: {original_param.non_stick} != {converted_param.non_stick}",
        )
    if original_param.preset_value != converted_param.preset_value:
        return (
            False,
            f"Parameter preset value mismatch: {original_param.preset_value} != {converted_param.preset_value}",
        )
    if original_param.custom_input_name != converted_param.custom_input_name:
        return (
            False,
            f"Parameter custom input name mismatch: {original_param.custom_input_name} != {converted_param.custom_input_name}",
        )
    if original_param.command_parameter != converted_param.command_parameter:
        return (
            False,
            f"Parameter command parameter mismatch: {original_param.command_parameter} != {converted_param.command_parameter}",
        )
    if original_param.custom_parameter != converted_param.custom_parameter:
        return (
            False,
            f"Parameter custom parameter mismatch: {original_param.custom_parameter} != {converted_param.custom_parameter}",
        )
    if (
        original_param.override_output_parameter_name
        != converted_param.override_output_parameter_name
    ):
        return (
            False,
            f"Parameter override output parameter name mismatch: {original_param.override_output_parameter_name} != {converted_param.override_output_parameter_name}",
        )
    if original_param.override_parameter_name != converted_param.override_parameter_name:
        return (
            False,
            f"Parameter override parameter name mismatch: {original_param.override_parameter_name} != {converted_param.override_parameter_name}",
        )

    return True, "Parameters are identical"


def validate_condition_groups(
    original_group: OMConditionGroup, converted_group: OMConditionGroup
) -> tuple[bool, str]:
    """
    Validates that the original and converted condition groups are identical.

    Args:
        original_group (OMConditionGroup): The original condition group.
        converted_group (OMConditionGroup): The converted condition group.

    Returns:
        tuple: (bool, str) True if the condition groups are identical, False otherwise, with a message.
    """
    if original_group.operator != converted_group.operator:
        return (
            False,
            f"Condition group operator mismatch: {original_group.operator} != {converted_group.operator}",
        )
    result, message = validate_lists(
        original_group.conditions, converted_group.conditions, validate_conditions
    )
    if not result:
        return False, f"Condition group conditions mismatch: {message}"

    return True, "Condition groups are identical"


def validate_conditions(
    original_condition: OMCondition, converted_condition: OMCondition
) -> tuple[bool, str]:
    """
    Validates that the original and converted conditions are identical.

    Args:
        original_condition (OMCondition): The original condition.
        converted_condition (OMCondition): The converted condition.

    Returns:
        tuple: (bool, str) True if the conditions are identical, False otherwise, with a message.
    """
    if original_condition.parameter_name != converted_condition.parameter_name:
        return (
            False,
            f"Condition parameter name mismatch: {original_condition.parameter_name} != {converted_condition.parameter_name}",
        )
    if original_condition.jsonpath != converted_condition.jsonpath:
        return (
            False,
            f"Condition jsonpath mismatch: {original_condition.jsonpath} != {converted_condition.jsonpath}",
        )
    if original_condition.regex != converted_condition.regex:
        return (
            False,
            f"Condition regex mismatch: {original_condition.regex} != {converted_condition.regex}",
        )
    if original_condition.skip_if_path_not_found != converted_condition.skip_if_path_not_found:
        return (
            False,
            f"Condition skip if path not found mismatch: {original_condition.skip_if_path_not_found} != {converted_condition.skip_if_path_not_found}",
        )

    return True, "Conditions are identical"


def validate_om_parameter_list(
    original_list: OMParameterList, converted_list: OMParameterList, validate_func: Any
) -> tuple[bool, str]:
    """
    Validates that the original and converted parameter lists are identical.

    Args:
        original_list (OMParameterList): The original parameter list.
        converted_list (OMParameterList): The converted parameter list.
        validate_func (function): The validation function to use for the parameters.

    Returns:
        tuple: (bool, str) True if the parameter lists are identical, False otherwise, with a message.
    """
    if len(original_list) != len(converted_list):
        return False, "Parameter list lengths do not match"

    for i, (original_param, converted_param) in enumerate(zip(original_list, converted_list)):
        result, message = validate_func(original_param, converted_param)
        if not result:
            return False, f"Parameter {i} mismatch: {message}"

    return True, "Parameter lists are identical"


def validate_lists(original_list, converted_list, validate_func) -> tuple[bool, str]:
    """
    Validates that the original and converted lists are identical.

    Args:
        original_list (list): The original list.
        converted_list (list): The converted list.
        validate_func (function): The validation function to use for the list elements.

    Returns:
        tuple: (bool, str) True if the lists are identical, False otherwise, with a message.
    """
    if original_list is None and converted_list is None:
        return True, "Lists are identical"
    if (original_list is None) != (converted_list is None):
        return False, "One of the lists is None while the other is not"
    if len(original_list) != len(converted_list):
        return False, "List lengths do not match"

    for i, (original_item, converted_item) in enumerate(zip(original_list, converted_list)):
        result, message = validate_func(original_item, converted_item)
        if not result:
            return False, f"List item {i} mismatch: {message}"

    return True, "Lists are identical"


""" Validate OMTree End """
