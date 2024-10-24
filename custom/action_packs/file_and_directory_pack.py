# custom/action_packs/file_and_directory_pack.py
import json
import os
from datetime import datetime, timezone

from src.om_cli.helpers.text_helpers import colorize_text
from src.om_cli.logger import get_logger as _get_logger
from src.om_cli.models.om_parameter import OMParameter, OMParameterType
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject

logger = _get_logger()

INFO_COLOR = "yellow"

PARAMETER_DEFINITIONS = {
    "file_path_to_file_string": {
        "file_path": {"direction": "input", "type": "STRING"},
        "file_string": {"direction": "output", "type": "STRING"},
    },
    "list_local_files": {"directory_path": {"direction": "input", "type": "STRING"}},
    "get_local_files_list": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "files_list": {"direction": "output", "type": "STRING"},
    },
    "prompt_user_to_choose_file": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "file_number": {"direction": "input", "type": "INTEGER"},
        "file_path": {"direction": "output", "type": "STRING"},
    },
    "store_api_response_to_timestamped_file": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "file_name": {"direction": "input", "type": "STRING"},
        "file_extension": {"direction": "input", "type": "STRING"},
        "result_file_path": {"direction": "output", "type": "STRING"},
        "result_file_content": {"direction": "output", "type": "STRING"},
    },
    "store_parameter_value_to_timestamped_file": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "file_name": {"direction": "input", "type": "STRING"},
        "parameter_value": {"direction": "input", "type": "STRING"},
        "file_extension": {"direction": "input", "type": "STRING"},
        "result_file_path": {"direction": "output", "type": "STRING"},
        "result_file_content": {"direction": "output", "type": "STRING"},
    },
    "create_empty_file": {
        "directory_path": {"direction": "input", "type": "STRING"},
        "file_name": {"direction": "input", "type": "STRING"},
        "file_path": {"direction": "output", "type": "STRING"},
    },
}


def file_path_to_file_string(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for converting a file path to a file string.

    OMParameters used:
        - file_path: The path to the file to convert to a string (Read)
        - file_string: The content of the file as a string (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If the file path is missing.
        Exception: If an unexpected error occurs while converting the file path to a file string.
    """
    try:
        (found_parameter, found_om_parameter) = action_parameters.get_om_parameter(
            "file_path", action_index
        )
        file_path = found_om_parameter.value if found_parameter else None

        repeat = False
        result_message = "File string read"

        if not file_path:
            raise ValueError("Missing file path")

        with open(file_path, "r", encoding="utf-8") as file:
            file_string = file.read()

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                type=OMParameterType.STRING,
                name=action_parameters.override_internal_action_parameter_name(
                    "file_string", action_index
                ),
                value=file_string,
                action_index=action_index,
            )
        )

        result_object = ResultObject(not repeat, result_message, None, om_parameters, repeat)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while converting the file path to a file string: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def get_local_files_list(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for getting the list of files from a directory.

    OMParameters used:
        - directory_path: The path to the directory to get the list of files from (Read)
        - files_list: The list of files in the directory (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If the directory path is missing.
        Exception: If an unexpected error occurs while getting the list of files from the directory.
    """
    try:
        (found_parameter, found_om_parameter) = action_parameters.get_om_parameter(
            "directory_path", action_index
        )
        directory_path = found_om_parameter.value if found_parameter else None

        result_message = "Files list read"

        if not directory_path:
            raise ValueError("Missing directory path")

        files = [
            f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))
        ]
        files_list = []

        for file_id, file in enumerate(files, start=1):
            file_dict = {
                "file_id": file_id,
                "file_name": file,
                "file_path": os.path.join(directory_path, file),
            }
            files_list.append(file_dict)

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                name=action_parameters.override_internal_action_parameter_name(
                    "files_list", action_index
                ),
                value=json.dumps(files_list),
                action_index=action_index,
            )
        )

        result_object = ResultObject(True, result_message, None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while getting the list of files from the directory: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def list_local_files(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for printing the files from a directory.

    OMParameters used:
        - directory_path: The path to the directory to print the files from (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no directory path is found.
        Exception: If an unexpected error occurs while printing the files from the directory.
    """
    try:
        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        directory_path = directory_path_parameter.value if found_directory_path_parameter else None

        if not directory_path:
            raise ValueError("Found no directory path to print files from")

        files = os.listdir(directory_path)
        print(f"Files in the directory {colorize_text(directory_path, INFO_COLOR)}:\n")

        for file_id, file in enumerate(files, start=1):
            print(colorize_text(f"[{file_id}] {file}", INFO_COLOR))
        print("\n")

        result_object = ResultObject(True, "Files printed", None, OMParameterList())
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while printing the files from the directory: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def prompt_user_to_choose_file(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for prompting the user to choose a file from a directory.

    OMParameters used:
        - directory_path: The path to the directory to choose a file from (Read)
        - file_number: The id of the chosen file (Created)
        - file_path: The path to the chosen file (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no directory path is found.
        Exception: If an unexpected error occurs while prompting the user to choose a file from the directory.
    """
    try:
        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        directory_path = directory_path_parameter.value if found_directory_path_parameter else None

        if not directory_path:
            raise ValueError("Found no directory path to choose a file from")

        files = os.listdir(directory_path)

        (found_file_number_parameter, file_number_parameter) = action_parameters.get_om_parameter(
            "file_number", action_index
        )
        file_number = file_number_parameter.value if found_file_number_parameter else None

        try:
            file_number = int(file_number)
        except ValueError as e:
            raise ValueError(
                f"The file_number parameter is not a valid number ({file_number})"
            ) from e

        if file_number < 1 or file_number > len(files):
            raise ValueError("Invalid file number")

        file_path = directory_path + files[file_number - 1]
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
        result_object = ResultObject(True, "User chose a file", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while prompting the user to choose a file from the directory: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def store_api_response_to_timestamped_file(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for storing the API response to a timestamped file.

    OMParameters used:
        - directory_path: The path to the directory to store the file in (Read)
        - file_name: The prefix to the name of the file to store (Read)
        - result_file_path: The path to the stored file (Created)
        - result_file_content: The content of the stored file (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no response object is found.
        Exception: If an unexpected error occurs while storing the response to a file.
    """
    try:
        if result_object.response is None:
            raise ValueError("No response object provided")

        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        if found_directory_path_parameter:
            directory_path = directory_path_parameter.value

        if not directory_path:
            raise ValueError("No directory_path provided")

        (found_file_name_parameter, file_name_parameter) = action_parameters.get_om_parameter(
            "file_name", action_index
        )
        file_name = (
            file_name_parameter.value if found_file_name_parameter else None
        ) or "api_response"

        (found_file_extension_parameter, file_extension_parameter) = (
            action_parameters.get_om_parameter("file_extension", action_index)
        )
        file_extension = (
            file_extension_parameter.value if found_file_extension_parameter else "json"
        )

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        file_path = directory_path + file_name + "_" + timestamp + "." + file_extension

        json_string = result_object.response.json()

        logger.debug("Storing a JSON file in the path: %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(json_string, file, indent=4)

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                name=action_parameters.override_internal_action_parameter_name(
                    "result_file_path", action_index
                ),
                value=file_path,
                action_index=action_index,
            )
        )
        om_parameters.add_parameter(
            OMParameter(
                type=OMParameterType.STRING,
                name=action_parameters.override_internal_action_parameter_name(
                    "result_file_content", action_index
                ),
                value=json.dumps(json_string, indent=4),
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


def store_parameter_value_to_timestamped_file(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for storing a parameter value to a timestamped file.

    OMParameters used:
        - directory_path: The path to the directory to store the file in (Read)
        - file_name: The prefix to the name of the file to store (Read)
        - file_extension: The extension of the file to store (Read)
        - parameter_value: The value of the parameter to store (Read)
        - result_file_path: The path to the stored file (Created)
        - result_file_content: The content of the stored file (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no parameter value is found.
        Exception: If an unexpected error occurs while storing the parameter value to a file.
    """
    try:
        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        directory_path = directory_path_parameter.value if found_directory_path_parameter else None

        if not directory_path:
            raise ValueError("No directory_path provided")

        (found_file_name_parameter, file_name_parameter) = action_parameters.get_om_parameter(
            "file_name", action_index
        )
        file_name = file_name_parameter.value if found_file_name_parameter else "parameter_value"

        (found_parameter_value_parameter, parameter_value_parameter) = (
            action_parameters.get_om_parameter("parameter_value", action_index)
        )
        parameter_value = (
            parameter_value_parameter.value if found_parameter_value_parameter else None
        )

        if not parameter_value:
            raise ValueError("No parameter_value provided")

        (found_file_extension_parameter, file_extension_parameter) = (
            action_parameters.get_om_parameter("file_extension", action_index)
        )
        file_extension = (
            file_extension_parameter.value if found_file_extension_parameter else "json"
        )

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        file_path = directory_path + file_name + "_" + timestamp + "." + file_extension

        logger.debug("Storing a parameter value in the path: %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(parameter_value)

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                name=action_parameters.override_internal_action_parameter_name(
                    "result_file_path", action_index
                ),
                value=file_path,
                action_index=action_index,
            )
        )
        om_parameters.add_parameter(
            OMParameter(
                type=OMParameterType.STRING,
                name=action_parameters.override_internal_action_parameter_name(
                    "result_file_content", action_index
                ),
                value=parameter_value,
                action_index=action_index,
            )
        )

        result_object = ResultObject(True, "Parameter value stored as a file", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while storing the parameter value to a file: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def create_empty_file(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for creating an empty file.

    OMParameters used:
        - directory_path: The path to the directory to create the file in (Read)
        - file_name: The name of the file to create (Read)
        - file_path: The path to the created file (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no file name is found.
        Exception: If an unexpected error occurs while creating the empty file.
    """
    try:
        (found_directory_path_parameter, directory_path_parameter) = (
            action_parameters.get_om_parameter("directory_path", action_index)
        )
        directory_path = directory_path_parameter.value if found_directory_path_parameter else None

        if not directory_path:
            raise ValueError("No directory_path provided")

        (found_file_name_parameter, file_name_parameter) = action_parameters.get_om_parameter(
            "file_name", action_index
        )
        file_name = file_name_parameter.value if found_file_name_parameter else "empty_file"

        file_path = directory_path + file_name

        logger.debug("Creating an empty file in the path: %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8"):
            pass

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

        result_object = ResultObject(True, "Empty file created", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while creating the empty file: {ex}",
            None,
            OMParameterList(),
        )

    return result_object
