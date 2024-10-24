# src/om_cli/helpers/text_helpers.py

from colors import color

from src.om_cli.logger import logger, logging
from src.om_cli.models.om_parameter_list import OMParameterList

INFO_COLOR = "yellow"
MAX_TEXT_LENGTH = 400


def colorize_text(title, color_name):
    """
    Colorizes the given title using the specified color.

    Args:
        title (str): The text to be colorized.
        color_name (str): The name of the color to be applied.

    Returns:
        str: The colorized text.

    """
    lines = str(title).split("\n")
    colored_lines = [color(line, fg=color_name) for line in lines]
    return "\n".join(colored_lines)


def debug_print_parameters(parameters: OMParameterList):
    """
    Debug function for printing the OMParameters.

    Args:
        parameters (OMParameterList): The parameters to print.

    Returns:
        None
    """
    debug_log = False
    for handler in logger.handlers:
        if handler.name == "stdout" and handler.level == logging.DEBUG:
            debug_log = True
            break

    if not debug_log:
        return

    if not parameters.has_items():
        print(colorize_text("No parameters found.", INFO_COLOR))
        return

    try:
        for parameter in parameters:
            parameter_text = f"Parameter: {colorize_text(parameter.name, INFO_COLOR)}"
            if parameter.override_parameter_name:
                parameter_text += f", Overrides the parameter: {colorize_text(parameter.override_parameter_name, INFO_COLOR)}"
            if parameter.custom_input_name:
                parameter_text += (
                    f", Custom input name: {colorize_text(parameter.custom_input_name, INFO_COLOR)}"
                )
            if parameter.type:
                parameter_text += (
                    f", Type: {colorize_text(f'{parameter.get_type_string()}', INFO_COLOR)}"
                )
            if parameter.default_value:
                parameter_text += (
                    f", Default value: {colorize_text(parameter.default_value, INFO_COLOR)}"
                )
            if parameter.command_parameter:
                parameter_text += f", Command parameter: {colorize_text('True', INFO_COLOR)}"
            if parameter.custom_parameter:
                parameter_text += f", Custom parameter: {colorize_text('True', INFO_COLOR)}"
            if parameter.override_output_parameter_name:
                parameter_text += (
                    f", Overrides the output parameter name: {colorize_text('True', INFO_COLOR)}"
                )
            if parameter.non_stick:
                parameter_text += f", Non-stick: {colorize_text('True', INFO_COLOR)}"
            if parameter.custom_text:
                parameter_text += (
                    f", Custom text: {colorize_text(parameter.custom_text, INFO_COLOR)}"
                )
            if parameter.api_parameter_name:
                parameter_text += f", API parameter name: {colorize_text(parameter.api_parameter_name, INFO_COLOR)}"
            if parameter.preset_value:
                parameter_text += (
                    f", Preset value: {colorize_text(parameter.preset_value, INFO_COLOR)}"
                )
            if parameter.value:
                value_length = len(str(parameter.value))
                if value_length < (MAX_TEXT_LENGTH + 1):
                    parameter_text += f", Value: {colorize_text(parameter.value, INFO_COLOR)}"
                else:
                    parameter_text += f"\nValue: {colorize_text(f'{parameter.value[:MAX_TEXT_LENGTH]}...({value_length})', INFO_COLOR)}"
            else:
                parameter_text += f", Value: {colorize_text('None', INFO_COLOR)}"

            parameter_text += (
                f", Action index: {colorize_text(str(parameter.action_index), INFO_COLOR)}"
            )

            print(parameter_text)
    except Exception as ex:
        print(colorize_text(f"An error occurred while printing the parameters: {ex}", INFO_COLOR))
        logger.error("An error occurred while printing the parameters: %s", ex)


def debug_print_text(text: str | None):
    """
    Debug function for potentally truncating and printing text.
    """
    debug_log = False
    for handler in logger.handlers:
        if handler.name == "stdout" and handler.level == logging.DEBUG:
            debug_log = True
            break

    if not debug_log:
        return

    if text is None:
        print(colorize_text("No provided text", INFO_COLOR))
    elif len(str(text)) < (MAX_TEXT_LENGTH + 1):
        print(colorize_text(text, INFO_COLOR))
    else:
        print(colorize_text(f"{text[:MAX_TEXT_LENGTH]}...({len(str(text))})", INFO_COLOR))
