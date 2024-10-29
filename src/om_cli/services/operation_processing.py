# src/om_cli/services/operation_processing.py

"""
This module contains functions for processing a chain of actions.
"""

import copy
import sys
from pathlib import Path

from consolemenu import Screen

from src.om_cli.handlers.api_handler import APIHandler
from src.om_cli.helpers.text_helpers import colorize_text, debug_print_parameters
from src.om_cli.logger import logger, logging
from src.om_cli.models.action_processing_state import OperationProcessingState
from src.om_cli.models.loop_state import LoopState
from src.om_cli.models.om_action import OMAction, OMActionType
from src.om_cli.models.om_operation import OMOperation
from src.om_cli.models.om_parameter import OMParameter, OMParameterType
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject
from src.om_cli.services.custom_components_processing import CustomComponents
from src.om_cli.services.parameter_processing import process_parameters

ERROR_COLOR = "red"
INFO_COLOR = "yellow"
PROMPT_COLOR = "orange"
TITLE_COLOR = "blue"

# Get the project base path from the current file path
SCRIPT_PATH = Path(__file__).resolve().parents[3]

# Generate the command prefix to run the CLI script
# Command: cd <project_base_path> && <python_executable> <script_name> -s <custom_arguments> -o <operation> <parameters>
COMMAND_PREFIX = f"cd {SCRIPT_PATH} && {sys.executable} -m src.om_cli -s"


def prompt_user(message: str, color: str):
    """Helper function to prompt user input with colorized text."""
    return Screen().input(colorize_text(message, color))


def process_operation(
    operation: OMOperation,
    argument_parameters: OMParameterList,
    custom_components: CustomComponents,
    skip_looping: bool = False,
):
    """
    The main function for processing a chain of actions in an operation.

    There are 3 types of actions:
        - API requests:
            API calls for using a REST API.
            Housed in the api_handler.py file.
        - Function calls:
            Calls to other functions in this file.
        - Loops:
            Loops are defined by two actions: OMActionType.LOOP_START and OMActionType.LOOP_END.
            Each loop action contains a loop index.
            When an OMActionType.LOOP_START action is encountered, the action index is stored together with the loop index.
            When an OMActionType.LOOP_END action is encountered, the user will be prompted to repeat the actions in the loop.
            If the user chooses to repeat, the current action index is set to the stored loop index,
             and the actions there after will thus be repeated.

    The actions are processed in order, and the result of each action is passed to the next action.
    The parameters from the previous actions are also passed to the next action so that they can be used through the whole chain of actions.

    Args:
        operation (Operation): The operation to process.
        base_actions (list[OMAction]): The actions to process.
        argument_parameters (OMParameterList): The parameters from the command-line arguments.
        skip_looping (bool): If set, looping will be skipped.

    Returns:
        ResultObject: The result object from the last action.
        state.parameter_history (OMParameterList): The history of the parameters.
        state.api_result_history[str]: The history of the API results.
        command: The generated command.
    Raises:
        Exception: If an unexpected error occurs while processing the actions.

    ToDo:
        - Add more detailed descriptions for used variables
    """
    operation_id = operation.operation_id
    operation_name = operation.menu_title
    logger.debug("Starting processing the operation: %s", operation_name)
    print(colorize_text(f"Processing the operation: {operation_name}", TITLE_COLOR))

    result_object = ResultObject(True, "", None, OMParameterList())
    api_handler = APIHandler(custom_components)
    state = OperationProcessingState(
        custom_components, api_handler
    )  # Initialize the action processing state
    actions = copy.deepcopy(operation.actions)  # Copy the actions to avoid modifying the original
    failed_processing = False

    state.add_extra_parameter(
        OMParameter(
            name="operation_id",
            type=OMParameterType.STRING,
            value=operation_id,
            action_index=-1,
        )
    )

    if actions is None:
        logger.error("The operation %s does not contain any actions", operation_name)
        prompt_user("\nPress enter to continue", ERROR_COLOR)
        return result_object, state.parameter_history, state.api_result_history, None

    while state.loop_state.get_action_index() < len(actions):
        action = actions[state.loop_state.get_action_index()]
        try:
            # print(colorize_text(f"- Processing the action {action.name}", TITLE_COLOR))
            logger.debug(
                "Processing the action %s (%s) of type %s",
                action.name,
                state.loop_state.get_action_index(),
                action.type,
            )

            # Evaluate conditions to decide whether to skip the action
            if should_skip_action(action, state.extra_parameters):
                logger.debug("Skipping the action %s based on the conditions", action.name)
                state.loop_state.increment_action_index()
                continue

            loop_result = process_looping(
                action,
                state.loop_state,
                state.extra_parameters,
                skip_looping,
                result_object.repeat_loop,
            )
            if loop_result == "continue":
                result_object.repeat_loop = None  # Reset the repeat loop flag
                continue
            elif loop_result == "break":
                failed_processing = True
                prompt_user("\nPress enter to continue", ERROR_COLOR)
                break

            logger.debug("Processing the action %s", action.name)
            debug_log_action_parameters(action, state.extra_parameters)

            # If the action has been run before during an argument run the user will be prompted for non-stick parameters
            is_repeated = state.is_action_repeated(action.name)

            process_parameters_result = ResultObject(True, "", None, OMParameterList())

            if action.parameters.has_items():
                process_parameters_result = process_parameters(
                    action.parameters,
                    argument_parameters,
                    state.extra_parameters,
                    is_repeated,
                    skip_looping,
                    state.loop_state.get_action_index(),
                )

            if (
                not process_parameters_result.success
                and process_parameters_result.text
                and process_parameters_result.text == "Aborted the Operation using CTRL + D"
            ):
                print(colorize_text("\nAborted the Operation using CTRL + D", ERROR_COLOR))
                prompt_user("\nPress enter to continue", ERROR_COLOR)
                failed_processing = True
                break

            if action.parameters.has_items() and not process_parameters_result.success:
                logger.error(
                    "Failed to process the parameters for the action %s: %s",
                    action.name,
                    process_parameters_result.text,
                )
                prompt_user("\nPress enter to continue", ERROR_COLOR)
                failed_processing = True
                break

            # In order not to manipulate the original parameters, we create a copy of the processed parameters
            processed_parameters = process_parameters_result.parameters.copy()

            # Since proccessed_parameters is the most current list, we want the values to come from there
            state.extra_parameters.merge(
                processed_parameters
            )  # Overwrite the old stored extra parameters with potentially updated values
            processed_parameters.merge(state.extra_parameters)

            result_object, status = process_action(
                action, processed_parameters, result_object, state
            )
            if status == "break":
                failed_processing = True
                prompt_user("\nPress enter to continue", ERROR_COLOR)
                break

            # Add the action to the history
            state.add_to_action_history(action.name)

            if result_object is not None and result_object.repeat_action:
                user_input = prompt_user(
                    f"\nThe action {action.name} resulted in:\n{result_object.text}\nDo you want to repeat the action? (y/n): ",
                    PROMPT_COLOR,
                )
                if user_input.lower() == "y":
                    logger.info(
                        "Repeating the %s action with the action index %s",
                        action.name,
                        state.loop_state.get_action_index(),
                    )
                    continue  # Repeat the same index

            state.parameter_history.merge(state.extra_parameters)

            if result_object is not None and (
                not result_object.success and action.failure_termination
            ):
                log_text = (
                    result_object.response.text if result_object.response else result_object.text
                )

                logger.error(
                    "Breaking the chain %s based on the result from the action %s (index %s) of the type %s: %s",
                    operation_id,
                    action.name,
                    state.loop_state.get_action_index(),
                    action.type,
                    log_text,
                )
                prompt_user("\nPress enter to continue", ERROR_COLOR)
                failed_processing = True
                break

            logger.debug(
                "Finished processing the action: %s [%s] of type %s",
                action.name,
                state.loop_state.get_action_index(),
                action.type,
            )
        except EOFError:
            logger.error(
                "Aborted the Operation using CTRL+D while processing the action %s [%s] of type %s",
                action.name,
                state.loop_state.get_action_index(),
                action.type,
            )
            result_object = ResultObject(
                False, "Aborted the Operation using CTRL+D", None, OMParameterList()
            )
            prompt_user("\nPress enter to continue", ERROR_COLOR)
            failed_processing = True
            break
        except Exception as ex:
            logger.error(
                "An unexpected error occurred while processing the action %s [%s] of type %s: %s",
                action.name,
                state.loop_state.get_action_index(),
                action.type,
                ex,
            )
            prompt_user("\nPress enter to continue", ERROR_COLOR)
            failed_processing = True
            break

        state.loop_state.increment_action_index()

    logger.debug("Finished processing the operation: %s", operation_name)
    command = None
    if not failed_processing:
        command = generate_command(operation_id, state.parameter_history, custom_components)
        print("\nCommand:\n" + colorize_text(f"{command}\n", INFO_COLOR))
        prompt_user("\nPress enter to continue", PROMPT_COLOR)

    return result_object, state.parameter_history, state.api_result_history, command


def should_skip_action(action: OMAction, om_parameters: OMParameterList) -> bool:
    """
    Evaluate the conditions for skipping an action.

    Args:
        action (OMAction): The action to evaluate.
        om_parameters (OMParameterList): The parameters to use in the evaluation.

    Returns:
        bool: True if the action should be skipped, False otherwise.
    """

    if action.skip_if_conditions:
        # Ensure all condition groups must evaluate to True for the action to be skipped
        return all(
            condition_group.evaluate(om_parameters) for condition_group in action.skip_if_conditions
        )
    return False


def process_action(
    action: OMAction,
    processed_parameters: OMParameterList,
    result_object: ResultObject,
    action_processing_state: OperationProcessingState,
) -> tuple[ResultObject, str]:
    """
    Process an action based on its type.

    Args:
        action (OMAction): The action to process.
        processed_parameters (OMParameterList): The processed parameters to use in the action.
        result_object (ResultObject): The result object from the previous action.
        action_processing_state (ActionProcessingState): The state of the action processing.

        Returns:
        ResultObject: The result object from the action.
        result: What to do when the action has been processed.
    """

    if action.type == OMActionType.API_REQUEST:
        result_object = action_processing_state.api_handler.process_api_request(
            action.name,
            processed_parameters,
            action_processing_state.loop_state.get_action_index(),
        )
        if result_object.parameters.has_items():
            action_processing_state.extra_parameters.merge(result_object.parameters)
        if not result_object.success:
            # Some API Requests are not critical and have other ways of being handled, so we do not want to break the chain if they fail.
            # But we still want to log the failure.
            logger.warning(
                "The API request for the action %s resulted in a non successful HTTP response: %s",
                action.name,
                result_object.text,
            )
        if result_object and result_object.response and result_object.response.text:
            action_processing_state.add_to_api_result_history(result_object.response.text)
        else:
            action_processing_state.add_to_api_result_history(result_object.text)
    elif action.type == OMActionType.FUNCTION_CALL:
        if (
            action_definition
            := action_processing_state.get_custom_components().get_action_definition(action.name)
        ):
            logger.debug(
                "The action definition %s was found in the loaded the Action packs",
                action.name,
            )
            result_object = action_definition["function"](
                result_object,
                processed_parameters,
                action_processing_state.loop_state.get_action_index(),
            )
            if result_object.parameters.has_items():
                action_processing_state.extra_parameters.merge(result_object.parameters)
        else:
            logger.error(
                "The action %s was not found in the loaded Action packs, check the Operation Tree Action spelling",
                action.name,
            )
            prompt_user("\nPress enter to continue", ERROR_COLOR)
            return result_object, "break"
    else:
        logger.error("Unknown action type %s", action.type)
        prompt_user("\nPress enter to continue", ERROR_COLOR)
        return result_object, "break"

    return result_object, ""


def process_looping(
    action: OMAction,
    loop_state: LoopState,
    parameters: OMParameterList,
    skip_looping: bool,
    repeat_loop: bool = None,
) -> str:
    """
    Process the looping actions.

    Args:
        action (OMAction): The action to process.
        loop_state (LoopState): The state of the loop.
        skip_looping (bool): If set, looping will be skipped.
        repeat_loop (bool | None): If True, the loop will be repeated based on previous input, if False, the loop will be skipped.

    Returns:
        result: The loop result.
    """
    # We do not have to go through the whole action process the action is a loop and skip_looping is active
    if skip_looping and action.type in [OMActionType.LOOP_START, OMActionType.LOOP_END]:
        logger.debug("Skipping the loop %s since skip_looping is active", action.name)
        loop_state.increment_action_index()
        return "continue"

    if repeat_loop is not None:
        if action.loop_number is None:
            raise ValueError(
                f"The action {OMAction.name} does not contain a loop number so repeat loop can not be used, check the Operation Tree"
            )

        if repeat_loop:
            logger.debug("Repeating the loop %s based on previous input", action.name)
            loop_state.set_action_index(
                loop_state.get_loop_start(action.loop_number)
            )  # Jump back to the start of the loop
            return "continue"
        else:
            logger.debug("Continuing past the loop %s based on previous input", action.name)
            loop_state.pop_loop_stack()
            loop_state.increment_action_index()
            return "continue"

    if action.type == OMActionType.LOOP_START:
        logger.debug(
            "Starting the loop %s on the action index %s",
            action.name,
            loop_state.get_action_index(),
        )
        if (
            action.loop_number not in loop_state.loop_stack
        ):  # Check if this loop start is already on the stack
            loop_state.add_loop_start(action.loop_number, loop_state.get_action_index())
            loop_state.push_loop_stack(
                action.loop_number
            )  # Push current loop index onto the stack only if not repeating
        loop_state.increment_action_index()
        return "continue"
    elif action.type == OMActionType.LOOP_END:
        if (
            loop_state.peek_loop_stack() == action.loop_number
        ):  # Check if this is the correct loop end
            repeat_loop_text = f"Do you want to repeat the loop {action.name}?"
            if action.custom_loop_repeat_prompt:
                repeat_loop_text = action.custom_loop_repeat_prompt
            repeat_loop_prompt_success = False
            while not repeat_loop_prompt_success:
                user_input = prompt_user(f"{repeat_loop_text} (y/n): ", PROMPT_COLOR)
                if user_input.lower() == "y":
                    logger.debug(
                        "Repeating %s from the action index %s jumping from %s",
                        action.name,
                        loop_state.get_loop_start(action.loop_number),
                        loop_state.get_action_index(),
                    )
                    loop_state.set_action_index(
                        loop_state.get_loop_start(action.loop_number)
                    )  # Jump back to the start of the loop
                    repeat_loop_prompt_success = True
                elif user_input.lower() == "n":
                    loop_state.pop_loop_stack()  # Pop this loop off the stack
                    loop_state.increment_action_index()
                    repeat_loop_prompt_success = True
                    logger.debug(
                        "Continuing past %s to the the action index %s",
                        action.name,
                        loop_state.get_action_index(),
                    )
                else:
                    print(colorize_text("Invalid input, please enter 'y' or 'n'", ERROR_COLOR))
        else:
            logger.error("Loop end without matching start for loop %s", action.loop_number)
            prompt_user("\nPress enter to continue", ERROR_COLOR)
            return "break"
        return "continue"
    return ""


def generate_command(operation_id, prepared_parameters, custom_components):
    """
    Generates a command string based on the given operation ID and prepared parameters.
    Used be able to skip the CLI navigation and instead perform an operation directly without having to interact with the CLI.

    Args:
        operation_id (str): The ID of the operation.
        prepared_parameters (list): A list of prepared parameters.
        custom_components (CustomComponents): The custom components object, in order to get used arguments.

    Returns:
        str: The generated command string.
    """

    command = f"{COMMAND_PREFIX}"

    argument_custom_path = custom_components.get_argument_custom_path()
    if argument_custom_path:
        command += f' -c "{argument_custom_path}"'

    argument_om_tree_file_path = custom_components.get_argument_om_tree_file_path()
    if argument_om_tree_file_path:
        command += f' -t "{argument_om_tree_file_path}"'

    argument_mock_api_responses_file_path = (
        custom_components.get_argument_mock_api_responses_file_path()
    )
    if argument_mock_api_responses_file_path:
        command += f' -m "{argument_mock_api_responses_file_path}"'

    command += f' -o "{operation_id}"'

    if prepared_parameters:
        for om_parameter in prepared_parameters:
            if not om_parameter.command_parameter:
                continue

            command += f" {om_parameter.name}="

            value = om_parameter.value

            if om_parameter.type == OMParameterType.STRING:
                value = f'"{value}"'

            command += f"{value}"

    return command


def debug_log_action_parameters(action: OMAction, extra_parameters: OMParameterList):
    """
    Log the action parameters in the terminal for debugging purposes.

    Args:
        action (OMAction): The action to log.
        extra_parameters (OMParameterList): The extra parameters to log.
    """
    debug_log = False
    for handler in logger.handlers:
        if handler.name == "stdout" and handler.level == logging.DEBUG:
            debug_log = True
            break

    if not debug_log:
        return

    # logger.debug("The action contains the parameters %s and the extracted parameters from previous actions: %s", action.parameters, extra_parameters)
    print(colorize_text("\nProcessing action parameters: ", TITLE_COLOR))
    debug_print_parameters(action.parameters)
    print(colorize_text("\nProcessing extra_parameters parameters: ", TITLE_COLOR))
    debug_print_parameters(extra_parameters)
