# src/om_cli/services/parameter_processing.py

import copy
import sys
from typing import List

from consolemenu import Screen

from src.om_cli.helpers.text_helpers import colorize_text, debug_print_text
from src.om_cli.logger import logger
from src.om_cli.models.om_action import OMAction
from src.om_cli.models.om_operation import OMOperation
from src.om_cli.models.om_parameter import OMParameter, OMParameterType
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject

ERROR_COLOR = "red"
INFO_COLOR = "yellow"
STANDARD_PROMPT_COLOR = "orange"


def check_actions_for_parameters(actions: List[OMAction]):
    """
    Checks the actions for parameters and returns a list of parameters.
    """
    parameter_dict = {}
    for action in actions:
        if action.parameters.has_items():
            for parameter in action.parameters:
                if parameter.name not in parameter_dict:
                    parameter_dict[parameter.name] = OMParameter(
                        name=parameter.name, type=parameter.type
                    )
                else:
                    parameter_dict[parameter.name].type = parameter.type
    return list(parameter_dict.values())


def verify_arguments(arguments, operation: OMOperation):
    """
    Verifies the arguments provided for a given operation.

    Args:
        arguments (list): The arguments provided by the user.
        operation (OMOperation): The operation object containing the actions and parameters.

    Returns:
        list: A list of OMParameter objects representing the validated arguments.

    Raises:
        SystemExit: If invalid arguments are provided.

    """
    operation_parameters = check_actions_for_parameters(operation.actions or [])
    if not arguments and not operation_parameters:
        logger.debug("The command %s does not require any parameters", operation.operation_id)
        return None

    is_invalid = False
    om_parameters = OMParameterList()

    try:
        for action_index, action in enumerate(operation.actions or []):
            if action.parameters.has_items():
                for parameter in action.parameters:
                    if any(p.name == parameter.name for p in om_parameters):
                        continue

                    found = False

                    if not parameter.command_parameter:
                        logger.debug(
                            "The parameter %s is not a command parameter, skipping validation",
                            parameter.name,
                        )
                        continue

                    (found, is_invalid, om_parameter) = validate_parameter_argument(
                        arguments, parameter
                    )

                    if found and not is_invalid:
                        om_parameters.add_parameter(om_parameter)

                    if not found:
                        print(
                            colorize_text(
                                f"The parameter {parameter.name} of the type {parameter.get_type_string()} is required for {operation.operation_id}.",
                                ERROR_COLOR,
                            )
                        )
                        is_invalid = True
    except Exception as ex:
        logger.error("An error occurred while verifying the arguments. Exiting: %s", ex)
        sys.exit()

    if is_invalid:
        print(colorize_text("Invalid arguments provided. Exiting.", ERROR_COLOR))
        sys.exit()

    return om_parameters


def validate_parameter_argument(arguments, parameter):
    """
    Validates the argument for a given parameter.

    Args:
        arguments (dict): A dictionary containing the arguments.
        parameter(str): The parameter to validate.

    Returns:
        tuple: A tuple containing three elements:
            - found (bool): Indicates whether the parameter was found in the arguments.
            - is_invalid (bool): Indicates whether the parameter value is invalid.
            - om_parameter (OMParameter): An instance of the OMParameter class representing the validated parameter.
    """
    om_parameter = None
    found = False
    is_invalid = False
    for key, value in arguments.items():
        validated_value = None
        if key == parameter.name:
            found = True

            valid, validated_value, error = validate_and_convert_parameter_value(
                value, parameter.type
            )
            if not valid:
                print(colorize_text(error, ERROR_COLOR))
                logger.warning("Invalid input for parameter %s: %s", parameter.name, error)
                is_invalid = True
                break
            # TODO: Currently OMParameter.value must be string so the validated is not used, add support for other types?
            om_parameter = OMParameter(
                name=parameter.name,
                type=parameter.type,
                value=value,
                action_index=parameter.action_index,
            )
            break

    return (found, is_invalid, om_parameter)


def check_for_provided_parameters(
    om_parameter: OMParameter,
    input_name: str,
    argument_parameters: OMParameterList,
    extra_parameters: OMParameterList,
    action_index: int,
    is_repeated: bool,
    skip_looping: bool,
):
    """
    Processes the parameters and updates the om_parameter value based on the provided arguments and extra parameters.
    """

    def find_and_update_parameter(parameters, param_type):
        found, found_om_parameter = parameters.get_om_parameter(input_name, action_index)
        if found:
            logger.debug(
                "Found %s parameter for %s and injected the value %s",
                param_type,
                input_name,
                found_om_parameter.value,
            )
            debug_print_text(found_om_parameter.value)
            om_parameter.value = found_om_parameter.value
            # TODO: Verify which parameter properties should be copied
            if found_om_parameter.command_parameter:
                om_parameter.command_parameter = found_om_parameter.command_parameter
            return True
        else:
            logger.debug(
                "The parameter %s is not found in the %s parameter list",
                input_name,
                param_type,
            )
        return False

    if (
        argument_parameters
        and (skip_looping or not om_parameter.non_stick or not is_repeated)
        and find_and_update_parameter(argument_parameters, "argument")
    ):
        return True

    if extra_parameters and (not om_parameter.non_stick or not is_repeated):  # Remove Is repeated?
        if find_and_update_parameter(extra_parameters, "extra"):
            return True
    else:
        logger.debug(
            "The parameter %s is of a non-stick type so it will not fill in the value based on previous input",
            input_name,
        )
    return False


def process_parameters(
    om_parameters,
    argument_parameters,
    extra_parameters,
    is_repeated,
    skip_looping,
    action_index,
):
    """
    Process the OM parameters as well as provided arguments by prompting the user for input when needed and validating the input values.

    Args:
        om_parameters (OMParameterList): List of OMParameter objects representing the parameters to be processed.
        argument_parameters (OMParameterList): List of OMParameter objects representing the parameters passed as command line arguments.
        extra_parameters (OMParameterList): List of OMParameter objects representing additional parameters.
        is_repeated (bool): Is true if the current actions has been run before during this session.
            Indicates whether prefilled arguments should be overridden if a loop is repeated.
        skip_looping (bool): Indicates whether the looping should be skipped.
        action_index (int): The index of the action that the parameter belongs to.

    Returns:
        ResultObject: An object containing the result of the parameter processing, including the processed OM parameters.

    Raises:
        Exception: If an error occurs while processing the parameters.

    ToDo:
        Describe the input parameters in more detail and what they are used for
    """

    def handle_user_input(om_parameter, default_value, value_prompt_text):
        for _ in range(20):
            user_input = Screen().input(value_prompt_text) or default_value or ""
            print("\n")
            valid, validated_value, error = validate_and_convert_parameter_value(
                user_input, om_parameter.type
            )
            if valid:
                return validated_value
            print(colorize_text(error, ERROR_COLOR))
            logger.warning("Invalid input for parameter %s: %s", om_parameter.name, error)
        raise RecursionError("Infinite loop detected while processing the parameters")

    result_object = None

    try:
        for om_parameter in om_parameters:
            if om_parameter.name == "operation_id":
                # Will not change during the operation run
                continue

            om_parameter.action_index = om_parameter.action_index or action_index

            om_parameter_copy = replace_placeholders(
                om_parameter, om_parameters, argument_parameters, extra_parameters
            )

            prompt_parts = [
                om_parameter_copy.custom_text or f"Please enter {om_parameter.name}",
                f"[{om_parameter_copy.get_type_string()}]",
            ]
            if om_parameter_copy.default_value:
                prompt_parts.append(
                    f"(default: {colorize_text(om_parameter_copy.default_value, INFO_COLOR)})"
                )
            value_prompt_text = colorize_text(" ".join(prompt_parts), STANDARD_PROMPT_COLOR) + ": "

            input_name = om_parameter_copy.custom_input_name or om_parameter.name

            if om_parameter_copy.custom_input_name:
                logger.debug(
                    "The parameter %s has a custom input name %s",
                    om_parameter.name,
                    om_parameter_copy.custom_input_name,
                )

            if check_for_provided_parameters(
                om_parameter,
                input_name,
                argument_parameters,
                extra_parameters,
                action_index,
                is_repeated,
                skip_looping,
            ):
                continue

            if om_parameter_copy.preset_value is not None:
                om_parameter.value = om_parameter_copy.preset_value
                logger.debug(
                    "The parameter %s has a preset value %s",
                    input_name,
                    om_parameter.value,
                )
                continue

            if om_parameter.override_output_parameter_name:
                # Since output parameters should not promt for user input before the action is run we have to indicate that
                #  this is an override_output_parameter_name if we have the parameter in the OMTree.
                logger.debug(
                    "The parameter %s is an output parameter and its name is overriding the internal name %s",
                    om_parameter.name,
                    om_parameter.override_parameter_name,
                )
                continue

            om_parameter.value = handle_user_input(
                om_parameter, om_parameter_copy.default_value, value_prompt_text
            )

        result_object = ResultObject(True, "", None, om_parameters)
    except EOFError:
        result_object = ResultObject(
            False, "Aborted the Operation using CTRL+D", None, OMParameterList()
        )
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An error occurred while processing the parameters: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def replace_placeholders(
    om_parameter: OMParameter,
    om_parameters: OMParameterList,
    argument_parameters: OMParameterList,
    extra_parameters: OMParameterList,
) -> OMParameter:
    """
    Replaces the placeholders {{XXX}} in parameter properties with values from other parameters.
    Checks the parameter properties: value, custom_text, custom_input_name, default_value, preset_value for placeholders.

    Args:
        om_parameter (OMParameter): The parameter to replace the placeholders in.
        om_parameters (OMParameterList): The list of OMParameter objects to use for replacing the placeholders.
        argument_parameters (OMParameterList): Additional list of OMParameter objects to use for replacing the placeholders.
        extra_parameters (OMParameterList): Extra list of OMParameter objects to use for replacing the placeholders.

    Returns:
        OMParameter: The modified parameter with placeholders replaced.

    Raises:
        Exception: If an error occurs while replacing the placeholders.
    """
    try:
        # Create a deep copy of the om_parameter
        om_parameter_copy = copy.deepcopy(om_parameter)

        for property_name in [
            "value",
            "custom_text",
            "custom_input_name",
            "default_value",
            "preset_value",
        ]:
            if not hasattr(om_parameter_copy, property_name):
                continue

            property_value = getattr(om_parameter_copy, property_name)
            if not property_value:
                continue

            if isinstance(property_value, str):
                placeholders = [ph for ph in property_value.split("{{") if "}}" in ph]
                placeholders = [ph.split("}}")[0] for ph in placeholders]
            else:
                placeholders = []

            for placeholder in placeholders:
                found = False
                for parameter_list in [
                    om_parameters,
                    argument_parameters,
                    extra_parameters,
                ]:
                    for parameter in parameter_list:
                        if parameter.name == placeholder:
                            found = True
                            if parameter.value is not None:
                                new_value = property_value.replace(
                                    f"{{{{{placeholder}}}}}", str(parameter.value)
                                )
                                if new_value != property_value:
                                    logger.debug(
                                        "Replaced the placeholder in the property %s on the parameter %s: %s -> %s",
                                        property_name,
                                        om_parameter_copy.name,
                                        property_value,
                                        new_value,
                                    )
                                    setattr(om_parameter_copy, property_name, new_value)
                            else:
                                logger.warning(
                                    "Found placeholder %s in the property %s on the parameter %s but the parameter value is None",
                                    placeholder,
                                    property_name,
                                    om_parameter_copy.name,
                                )
                            break
                    if found:
                        break

                if not found:
                    limit = 50
                    placeholder = (
                        (placeholder[:limit] + "...") if len(placeholder) > limit else placeholder
                    )
                    logger.warning(
                        "No parameter found for placeholder %s in the property %s on the parameter %s",
                        placeholder,
                        property_name,
                        om_parameter_copy.name,
                    )

        return om_parameter_copy

    except Exception as ex:
        raise Exception(f"An error occurred while replacing the placeholders: {ex}") from ex


def validate_and_convert_parameter_value(user_input, input_type):
    """
    Validates and converts the provided parameter value into a valid format based on the specified input type.

    Args:
        user_input (str): The user input to be validated and converted.
        input_type (OMParameterType): The type of the parameter to validate against.

    Returns:
        tuple: A tuple containing:
            - success (bool): Indicates whether the validation and conversion were successful.
            - value: The converted value if successful, otherwise None.
            - error (str): An error message if validation fails, otherwise an empty string.
    """

    type_handlers = {
        OMParameterType.STRING: lambda x: (True, x, ""),
        OMParameterType.BOOLEAN: lambda x: (
            x.lower() in ["true", "false"],
            x.lower() == "true",
            f"{x} is not a valid boolean value.",
        ),
        OMParameterType.INTEGER: lambda x: (
            (x.isdigit(), int(x), "")
            if x.isdigit()
            else (False, None, f"{x} is not a valid integer.")
        ),
    }

    try:
        if type_handler := type_handlers.get(input_type):
            return type_handler(user_input)
        return False, None, f"{input_type} is currently not supported."
    except ValueError:
        return (
            False,
            None,
            f"Invalid {input_type} value. Please provide a valid {input_type}.",
        )
    except Exception as ex:
        return (
            False,
            None,
            f"Unable to convert the input {user_input} into a usable format - {ex}",
        )
