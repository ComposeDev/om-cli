# custom/action_packs/json_pack.py
import json
import os
import re

from rich import print as _rich_print
from rich.tree import Tree

from src.om_cli.logger import get_logger as _get_logger
from src.om_cli.models.om_parameter import OMParameter, OMParameterType
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject

logger = _get_logger()

TREE_COLOR = "green"

PARAMETER_DEFINITIONS = {
    "store_result_to_json_file": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "identifier": {"direction": "input", "type": "STRING"},
        "file_path": {"direction": "output", "type": "STRING"},
    },
    "store_json_string_to_json_file": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "identifier": {"direction": "input", "type": "STRING"},
        "json_string": {"direction": "input", "type": "STRING"},
        "file_path": {"direction": "output", "type": "STRING"},
    },
    "store_json_string_to_custom_json_file": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "file_name": {"direction": "input", "type": "STRING"},
        "json_string": {"direction": "input", "type": "STRING"},
        "file_path": {"direction": "output", "type": "STRING"},
    },
    "extract_field_from_json_string": {
        "field_name": {"direction": "input", "type": "STRING"},
        "json_string": {"direction": "input", "type": "STRING"},
        "extracted_json_field_value": {"direction": "output", "type": "STRING"},
    },
    "extract_object_from_json_list": {
        "identifier": {"direction": "input", "type": "STRING"},
        "id_field": {"direction": "input", "type": "STRING"},
        "object_field": {"direction": "input", "type": "STRING"},
        "json_string": {"direction": "input", "type": "STRING"},
        "extracted_json_object": {"direction": "output", "type": "STRING"},
    },
    "present_simple_json_tree": {
        "json_string": {"direction": "input", "type": "STRING"},
        "node_name_field": {"direction": "input", "type": "STRING"},
        "parent_field": {"direction": "input", "type": "STRING"},
    },
}


def store_result_to_json_file(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for storing the result to a JSON file.

    OMParameters used:
        - identifier: The identifier of the file to store (Read)
        - response: The response object to store (Read)
        - file_path: The path to the stored file (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no response object is found.
        Exception: If an unexpected error occurs while storing the response to a file.
    """
    try:
        if not result_object.response:
            raise ValueError("No JSON response to store to file")

        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        if found_directory_path_parameter:
            directory_path = directory_path_parameter.value

        if not directory_path:
            raise ValueError("No directory_path provided")

        (found_parameter, identifier_parameter) = action_parameters.get_om_parameter(
            "identifier", action_index
        )
        file_name = identifier_parameter.value if found_parameter else "api_response"

        if not found_parameter:
            logger.warning("No identifier provided, storing the response as %s", file_name)

        file_path = directory_path + file_name + ".json"

        json_string = result_object.response.json()

        logger.debug("Storing a JSON file in the path: %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        processed_json_value = json_string.encode("utf-8").decode("unicode_escape")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(processed_json_value)

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                name=action_parameters.override_internal_action_parameter_name(
                    "file_path", action_index
                ),
                value=file_path,
                action_index=action_index,
            )
        )

        result_object = ResultObject(True, "Result stored as a JSON file", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while storing the response to JSON file: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def store_json_string_to_json_file(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for storing a JSON string to a JSON file.

    OMParameters used:
        - identifier: The identifier of the file to store (Read)
        - json_string: The JSON string to store (Read)
        - file_path: The path to the stored file (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no JSON string is found.
        Exception: If an unexpected error occurs while storing the JSON string to a file.
    """
    try:
        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        if found_directory_path_parameter:
            directory_path = directory_path_parameter.value

        if not directory_path:
            raise ValueError("No directory_path provided")

        file_name = "json_string"
        (found_parameter, identifier_parameter) = action_parameters.get_om_parameter(
            "identifier", action_index
        )
        file_name = identifier_parameter.value if found_parameter else "api_response"

        if not found_parameter:
            logger.warning("No identifier provided, storing the response as %s", file_name)

        file_path = directory_path + file_name + ".json"

        (found_parameter, found_om_parameter) = action_parameters.get_om_parameter(
            "json_string", action_index
        )
        json_value = found_om_parameter.value if found_parameter else None

        if not found_parameter:
            raise ValueError("Found no JSON string to store to file")

        logger.debug("Storing a JSON file in the path: %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        processed_json_value = json_value.encode("utf-8").decode("unicode_escape")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(processed_json_value)

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                name=action_parameters.override_internal_action_parameter_name(
                    "file_path", action_index
                ),
                value=file_path,
                action_index=action_index,
            )
        )
        result_object = ResultObject(True, "Result stored as a JSON file", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while storing the response to JSON file: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def store_json_string_to_custom_json_file(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for storing a JSON string to a custom named JSON file.

    OMParameters used:
        - file_name: The name of the file to store (Read)
        - json_string: The JSON string to store (Read)
        - file_path: The path to the stored file (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no JSON string is found.
        Exception: If an unexpected error occurs while storing the JSON string to a file.
    """
    try:
        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        if found_directory_path_parameter:
            directory_path = directory_path_parameter.value

        if not directory_path:
            raise ValueError("No directory_path provided")

        file_name = "json_string"
        (found_file_name_parameter, file_name_parameter) = action_parameters.get_om_parameter(
            "file_name", action_index
        )
        file_name = file_name_parameter.value if found_file_name_parameter else "api_response"

        if not found_file_name_parameter:
            logger.warning("No file name provided, storing the JSON string as %s", file_name)

        file_path = directory_path + file_name + ".json"

        (found_parameter, found_om_parameter) = action_parameters.get_om_parameter(
            "json_string", action_index
        )
        json_value = found_om_parameter.value if found_parameter else None

        if not found_parameter:
            raise ValueError("Found no JSON string to store to file")

        logger.debug("Storing a JSON file in the path: %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        processed_json_value = json_value.encode("utf-8").decode("unicode_escape")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(processed_json_value)

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                name=action_parameters.override_internal_action_parameter_name(
                    "file_path", action_index
                ),
                value=file_path,
                action_index=action_index,
            )
        )

        result_object = ResultObject(True, "Result stored as a JSON file", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while storing the response to JSON file: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def extract_field_from_json_string(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for extracting a field from a JSON string.

    OMParameters used:
        - field_name: The name of the field to extract (Read)
        - json_string: The JSON string to extract the field from (Read)
        - extracted_json_field_value: The extracted field as a string (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If the field name or JSON string is missing.
        Exception: If an unexpected error occurs while extracting the field.
    """
    try:
        (found_parameter, found_om_parameter) = action_parameters.get_om_parameter(
            "field_name", action_index
        )
        field_name = found_om_parameter.value if found_parameter else None

        (found_parameter, found_om_parameter) = action_parameters.get_om_parameter(
            "json_string", action_index
        )
        json_string = found_om_parameter.value if found_parameter else None

        repeat = False
        result_message = "Field extracted"

        if not field_name or not json_string:
            raise ValueError("Missing field name or JSON string")

        try:
            # Try to parse the input as JSON
            json_object = json.loads(json_string)
            extracted_field = json_object.get(field_name)
        except json.JSONDecodeError:
            # If parsing fails, treat the input as a plain string
            pattern = re.compile(rf'"{field_name}"\s*:\s*"([^"]+)"')
            match = pattern.search(json_string)
            extracted_field = match.group(1) if match else None

        om_parameters = OMParameterList()

        if extracted_field:
            om_parameters.add_parameter(
                OMParameter(
                    type=OMParameterType.STRING,
                    name=action_parameters.override_internal_action_parameter_name(
                        "extracted_json_field_value", action_index
                    ),
                    value=json.dumps(extracted_field, indent=4),
                    action_index=action_index,
                )
            )
        else:
            repeat = True
            extracted_field = None
            result_message = (
                'Unable to find the field "' + field_name + '" in the provided JSON string'
            )
            logger.error(result_message)

        result_object = ResultObject(not repeat, result_message, None, om_parameters, repeat)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while extracting the field: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def extract_object_from_json_list(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for extracting an object from a JSON list.

    OMParameters used:
        - identifier: The identifier of the object to extract (Read)
        - id_field: The field to use to find the identifier (Read)
        - object_field: The field to extract the object from (Read)
        - json_string: The JSON list string to extract the object from (Read)
        - extracted_json_object: The extracted object as a string (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If the identifier, id field, object field, or JSON list is missing.
        Exception: If an unexpected error occurs while extracting the object.
    """

    def extract_parameter(name, default=None):
        found, parameter = action_parameters.get_om_parameter(name, action_index)
        return parameter.value if found else default

    try:
        identifier = extract_parameter("identifier", None)
        id_field = extract_parameter("id_field", None)
        object_field = extract_parameter("object_field", None)
        json_list = extract_parameter("json_string", None)

        repeat = False
        result_message = "Object extracted"

        if not identifier or not id_field or not object_field or not json_list:
            raise ValueError("Missing identifier, id field, object field, or JSON list")

        json_list_object = json.loads(json_list)
        extracted_object = next(
            (
                json_object.get(object_field)
                for json_object in json_list_object
                if json_object.get(id_field) == identifier
            ),
            None,
        )
        om_parameters = OMParameterList()

        if extracted_object:
            om_parameters.add_parameter(
                OMParameter(
                    type=OMParameterType.STRING,
                    name=action_parameters.override_internal_action_parameter_name(
                        "extracted_json_object", action_index
                    ),
                    value=json.dumps(extracted_object, indent=4),
                    action_index=action_index,
                )
            )
        else:
            repeat = True
            extracted_object = None
            result_message = (
                'Unable to find the object with the identifier "'
                + identifier
                + '" in the provided JSON list'
            )
            logger.error(result_message)

        result_object = ResultObject(not repeat, result_message, None, om_parameters, repeat)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while extracting the object: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def present_simple_json_tree(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for presenting a simple json tree.

    OMParameters used:
        - json_string: The JSON string to present as a tree (Read)
        - node_name_field: The field to use as the node name (Read)
        - parent_field: The field to use to identify the parent node (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no stored json tree data is found.
        Exception: If an unexpected error occurs while presenting the json tree.
    """
    try:
        (found_json_string_parameter, json_string_parameter) = action_parameters.get_om_parameter(
            "json_string", action_index
        )
        json_tree_string = json_string_parameter.value if found_json_string_parameter else None

        (found_node_name_field_parameter, node_name_field_parameter) = (
            action_parameters.get_om_parameter("node_name_field", action_index)
        )
        node_name_field = (
            node_name_field_parameter.value if found_node_name_field_parameter else "None"
        )

        (found_parent_field_parameter, parent_field_parameter) = action_parameters.get_om_parameter(
            "parent_field", action_index
        )
        parent_field = parent_field_parameter.value if found_parent_field_parameter else None

        if not json_tree_string or not node_name_field or not parent_field:
            raise ValueError("Missing JSON string, node name field, or parent field")

        tree_object = _generate_tree(json_tree_string, node_name_field, parent_field)
        _rich_print(tree_object)
        result_object = ResultObject(True, "JSON tree presented", None, OMParameterList())
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while presenting the json tree: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


"""
Helper functions
"""


def _generate_tree(json_string: str, node_name_field: str, parent_field: str) -> Tree:
    """
    Generates a tree structure from a JSON string.

    Args:
        json_string (str): A JSON string representing the tree structure.
        node_name_field (str): The field to use as the node name.
        parent_field (str): The field to use as the parent field.

    Returns:
        Tree: The root node of the generated tree.

    """
    json_data = json.loads(json_string)
    # Create a mapping of each item to its parent
    parent_map = {item[node_name_field]: item.get(parent_field) for item in json_data}

    # Create a mapping of each id to its tree node
    tree_nodes = {
        item[node_name_field]: Tree(f"[{TREE_COLOR}]{item[node_name_field]}") for item in json_data
    }

    # Add each node to its parent in the tree
    for item in json_data:
        node = tree_nodes[item[node_name_field]]
        parent_id = parent_map[item[node_name_field]]
        if parent_id is None:
            # This node is a root node
            tree = node
        else:
            # This node has a parent, so add it to the parent node
            parent_node = tree_nodes.get(parent_id)
            if parent_node is not None:
                parent_node.add(node)

    if tree is None:
        raise ValueError("No root node found")

    return tree
