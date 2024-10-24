# custom/action_packs/common_pack.py
import json

from consolemenu import Screen
from rich import print_json as _print_json
from rich.console import Console
from rich.table import Table

from src.om_cli.helpers.text_helpers import colorize_text
from src.om_cli.logger import get_logger as _get_logger
from src.om_cli.models.om_parameter import OMParameter, OMParameterType
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject

logger = _get_logger()

INFO_COLOR = "yellow"
PROMPT_COLOR = "orange"

PARAMETER_DEFINITIONS = {
    "print_response": {},
    "print_parameter": {"parameter_value": {"direction": "input", "type": "STRING"}},
    "prompt_for_parameters": {},
    "prompt_for_yes_no": {
        "question": {"direction": "input", "type": "STRING"},
        "user_response_value": {"direction": "output", "type": "BOOLEAN"},
    },
    "replace_text": {
        "text": {"direction": "input", "type": "STRING"},
        "search_text": {"direction": "input", "type": "STRING"},
        "replace_text": {"direction": "input", "type": "STRING"},
        "replaced_text": {"direction": "output", "type": "STRING"},
    },
    "list_array_with_indexes": {
        "item_list": {"direction": "input", "type": "STRING"},
        "item_limit": {"direction": "input", "type": "INTEGER"},
        "list_node_fields": {"direction": "input", "type": "STRING"},
        "show_loop_alternative": {"direction": "input", "type": "BOOLEAN"},
        "loop_alternative_text": {"direction": "input", "type": "STRING"},
    },
    "prompt_user_to_choose_indexed_item": {
        "item_list": {"direction": "input", "type": "STRING"},
        "item_number": {"direction": "input", "type": "INTEGER"},
        "item_node_value": {"direction": "input", "type": "STRING"},
        "chosen_item_value": {"direction": "output", "type": "STRING"},
        "show_loop_alternative": {"direction": "input", "type": "BOOLEAN"},
    },
    "print_simple_json_list": {
        "json_list": {"direction": "input", "type": "STRING"},
        "list_node_fields": {"direction": "input", "type": "STRING"},
        "list_limit": {"direction": "input", "type": "INTEGER"},
        "list_text": {"direction": "input", "type": "STRING"},
    },
}


def print_response(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for printing the response of the previous API request.

    OMParameters used:
        - response: The response object to print (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no response object is found.
        Exception: If an unexpected error occurs while printing the response.
    """
    try:
        if result_object.response is None:
            raise ValueError("No response object provided")

        # Make sure that the response is JSON otherwise print the text without JSON color highlighting
        if result_object.response.headers.get("content-type") == "application/json":
            json_data = _parse_json(result_object.response.text, "Invalid JSON response")
            _print_json(data=json_data)
        elif result_object.response.text:
            print(colorize_text(f"\n{result_object.response.text}\n", INFO_COLOR))
        else:
            print(colorize_text("\nThe response contained no text\n", INFO_COLOR))
        result_object = ResultObject(True, "", None, OMParameterList())
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while printing the response: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def print_parameter(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for printing a parameter.
    Can use placeholders in the parameter_value string to reference other OMParameters.
        Use the format: {{parameter_name}} in the question string and name the OMParameter accordingly.

    OMParameters used:
        - parameter_value: The value of the parameter to print (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no parameter value is found.
        Exception: If an unexpected error occurs while printing the parameter.

    """
    try:
        parameter_value = _fetch_parameter("parameter_value", action_parameters, action_index)
        if not parameter_value:
            raise ValueError("Found no parameter value to print")

        try:
            # Check if the parameter value is JSON otherwise print the text without JSON color highlighting
            parameter_json_value = _parse_json(
                parameter_value, "The parameter does not seem to be of the JSON type"
            )
            logger.debug("The parameter seems to be of the JSON type")
            _print_json(data=parameter_json_value)
        except json.JSONDecodeError as ex:
            logger.debug(ex)
            print(colorize_text(f"\n{parameter_value}\n", INFO_COLOR))

        result_object = ResultObject(True, "", None, OMParameterList())
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while printing the parameter: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def prompt_for_parameters(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Dummy action to prompt for parameters and store the values as om parameters to be used later.
    Can be used to prompt for parameters before the action they are to be used.

    OMParameters used:
        - None

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        None
    """

    return ResultObject(
        True,
        "Dummy action to prompt for parameters before the action they are to be used",
        None,
        OMParameterList(),
    )


def prompt_for_yes_no(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for prompting the user with a yes/no question.
    The user can answer with 'y' or 'n' and the result will be stored in the result object.
    Can use placeholders in the question string to reference other OMParameters.
        Use the format: {{parameter_name}} in the question string and name the OMParameter accordingly.

    OMParameters used:
        - question: The question to ask the user (Read)
        - user_response_value (boolean): The value of the user response (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no question is found.
    """
    try:
        question = _fetch_parameter("question", action_parameters, action_index)
        if not question:
            raise ValueError("No question found")

        response_value = False
        user_answer = None
        while user_answer is None:
            user_answer = Screen().input(colorize_text(f"{question} (y/n): ", PROMPT_COLOR))

            if user_answer.lower() not in ["y", "n"]:
                print("Invalid answer, please answer with y or n")
                user_answer = None
            else:
                response_value = user_answer.lower() == "y"

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                type=OMParameterType.BOOLEAN,
                name=action_parameters.override_internal_action_parameter_name(
                    "user_response_value", action_index
                ),
                value=str(response_value),
                non_stick=True,
                action_index=action_index,
            )
        )

        result_object = ResultObject(True, "User answered the question", None, om_parameters)
    except ValueError as ex:
        result_object = ResultObject(
            False,
            f"An error occurred while prompting the user with a yes/no question: {ex}",
            None,
            OMParameterList(),
        )
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while prompting the user with a yes/no question: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def replace_text(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for replacing text in a string.

    OMParameters used:
        - text: The text to replace the text in (Read)
        - search_text: The text to search for (Read)
        - replace_text: The text to replace the search text with (Read)
        - replaced_text: The resulting text after the replacement (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no text, search text or replace text is found.
        Exception: If an unexpected error occurs while replacing text.
    """
    try:
        text = _fetch_parameter("text", action_parameters, action_index)
        search_text = _fetch_parameter("search_text", action_parameters, action_index)
        replace_text = _fetch_parameter("replace_text", action_parameters, action_index)

        if text is None or search_text is None or replace_text is None:
            raise ValueError("Either found no text, search text or replace text to replace")

        replaced_text = text.replace(search_text, replace_text)

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                type=OMParameterType.STRING,
                name=action_parameters.override_internal_action_parameter_name(
                    "replaced_text", action_index
                ),
                value=replaced_text,
                action_index=action_index,
            )
        )

        result_object = ResultObject(True, "", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while replacing text: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def prompt_user_to_choose_indexed_item(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for prompting the user to choose an item from a list.

    OMParameters used:
        - item_list: The list of items to choose from (Read)
        - item_number: The id of the chosen item (Created)
        - item_node_value: The name of the value field of the item to pass on to the om_parameter, defaults to the whole item (Read)
        - chosen_item_value: The value of the chosen item (Created)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no item list is found.
        Exception: If an unexpected error occurs while prompting the user to choose an item from the list.
    """
    try:
        item_list = _fetch_parameter("item_list", action_parameters, action_index)
        if not item_list:
            raise ValueError("Found no items to choose from")

        json_item_list = _parse_json(item_list, "Error decoding the item list")

        item_number_str = _fetch_parameter("item_number", action_parameters, action_index)
        if item_number_str == "":
            raise ValueError("Found no chosen item number")

        item_number = -1
        try:
            item_number = int(item_number_str)
        except ValueError as exc:
            raise ValueError(
                f"The item_number parameter is not a valid number ({item_number})"
            ) from exc

        if len(json_item_list) < item_number:
            raise ValueError(f"Item number out of range ({item_number}/{len(json_item_list)})")

        repeat_loop_response = None

        show_loop_alternative = (
            _fetch_parameter("show_loop_alternative", action_parameters, action_index) or "False"
        )
        if show_loop_alternative.lower() == "true" and item_number == 0:
            result_object = ResultObject(
                True,
                "User chose to continue searching",
                None,
                OMParameterList(),
                False,
                True,
            )
            return result_object
        if show_loop_alternative.lower() == "true" and item_number != 0:
            repeat_loop_response = False

        chosen_item = json_item_list[item_number - 1]

        item_node_value = _fetch_parameter("item_node_value", action_parameters, action_index)
        chosen_item_value = (
            chosen_item if item_node_value == "." else chosen_item.get(item_node_value)
        )

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                type=OMParameterType.STRING,
                name=action_parameters.override_internal_action_parameter_name(
                    "chosen_item_value", action_index
                ),
                value=json.dumps(chosen_item_value),
                action_index=action_index,
            )
        )

        result_object = ResultObject(
            True, "User chose an item", None, om_parameters, False, repeat_loop_response
        )
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while prompting the user to choose an item from the list: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def list_array_with_indexes(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for printing an array with indices.

    OMParameters used:
        - item_list: The list of items to print with incremented numbers (Read)
        - item_limit: The maximum number of items to print, defaults to: 10 (Read)
        - item_node_name: The name field of the item to present in the list, defaults to the whole item (Read)
        - show_loop_alternative: Show an alternative to repeat the loop (Read)
        - loop_alternative_text: The text to display for the loop alternative (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no item list is found.
        Exception: If an unexpected error occurs while printing the items from the list.
    """
    try:
        found_item_list_parameter, item_list_parameter = action_parameters.get_om_parameter(
            "item_list", action_index
        )
        item_list = item_list_parameter.value if found_item_list_parameter else None
        if not item_list:
            raise ValueError("Found no items to print")

        json_item_list = _parse_json(item_list, "Error decoding the item list")

        item_limit_str = _fetch_parameter("item_limit", action_parameters, action_index) or "10"
        item_limit = -1
        try:
            item_limit = int(item_limit_str)
        except ValueError as exc:
            raise ValueError(
                f"The item_limit parameter is not a valid number ({item_limit})"
            ) from exc

        list_node_fields_value = _fetch_parameter(
            "list_node_fields", action_parameters, action_index
        )
        list_node_fields = list_node_fields_value.split(",") if list_node_fields_value else None

        show_loop_alternative = (
            _fetch_parameter("show_loop_alternative", action_parameters, action_index) or "False"
        )
        loop_alternative_text = (
            _fetch_parameter("loop_alternative_text", action_parameters, action_index)
            or "Continue searching"
        )

        if json_item_list:
            list_item_text = item_list_parameter.custom_text or "Items in the list"

            caption = ""
            if len(json_item_list) > item_limit:
                caption = (
                    f"Note: Only showing the first {item_limit} of {len(json_item_list)} items"
                )

            table = Table(title=list_item_text, caption=caption)

            table.add_column("Choice ID", justify="center", style="cyan")
            if list_node_fields:
                for field in list_node_fields:
                    table.add_column(
                        field.replace("_", " ").capitalize(),
                        justify="left",
                        style="green",
                    )
            else:
                table.add_column("Item", justify="left", style="green")

            for item_id, item in enumerate(json_item_list, start=1):
                if item_id > item_limit:
                    break

                table.add_row(
                    str(item_id),
                    *(
                        [item.get(field, "") for field in list_node_fields]
                        if list_node_fields
                        else [item]
                    ),
                )

            if show_loop_alternative.lower() == "true":
                table.add_section()
                table.add_row("0", loop_alternative_text)

            Console().print(table)
        else:
            print(colorize_text("The item list is empty / No results\n", INFO_COLOR))

        result_object = ResultObject(True, "Items printed", None, OMParameterList())
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while printing the items from the list: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def print_simple_json_list(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for printing a simple JSON list.

    OMParameters used:
        - json_list: The JSON list to print (Read)
        - list_node_fields: The fields to display in the list, defaults to the whole item (Read)
        - list_limit: The maximum number of items to print, defaults to: 10 (Read)
        - list_text: The text to display before the list (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no JSON list is found.
        Exception: If an unexpected error occurs while printing the JSON list.
    """
    try:
        json_list = _fetch_parameter("json_list", action_parameters, action_index)
        if not json_list:
            raise ValueError("Found no JSON list to print")

        json_item_list = _parse_json(json_list, "Error decoding the JSON list")

        list_node_fields_value = _fetch_parameter(
            "list_node_fields", action_parameters, action_index
        )
        list_node_fields = list_node_fields_value.split(",") if list_node_fields_value else None

        list_limit_str = _fetch_parameter("item_limit", action_parameters, action_index) or "10"
        list_limit = -1
        try:
            list_limit = int(list_limit_str)
        except ValueError as exc:
            raise ValueError(
                f"The list_limit parameter is not a valid number ({list_limit})"
            ) from exc

        list_text = (
            _fetch_parameter("list_text", action_parameters, action_index) or "Items in the list"
        )

        if json_item_list:
            caption = ""
            if len(json_item_list) > list_limit:
                caption = (
                    f"Note: Only showing the first {list_limit} of {len(json_item_list)} items"
                )

            table = Table(title=list_text, caption=caption)
            if list_node_fields:
                for field in list_node_fields:
                    table.add_column(
                        field.replace("_", " ").capitalize(),
                        justify="left",
                        style="green",
                    )
            else:
                table.add_column("Item", justify="left", style="green")

            for item_id, item in enumerate(json_item_list, start=1):
                if item_id > list_limit:
                    break

                table.add_row(
                    *(
                        [str(item.get(field, "")) for field in list_node_fields]
                        if list_node_fields
                        else [str(item)]
                    )
                )

            Console().print(table)
        else:
            print(colorize_text("The JSON list is empty / No results\n", INFO_COLOR))

        result_object = ResultObject(True, "JSON list printed", None, OMParameterList())
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while printing the JSON list: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


"""
Helper functions
"""


def _parse_json(data: str, error_message: str) -> dict:
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(error_message) from e


def _fetch_parameter(name: str, action_parameters: OMParameterList, action_index: int) -> str:
    found, parameter = action_parameters.get_om_parameter(name, action_index)
    return parameter.value if found else None
