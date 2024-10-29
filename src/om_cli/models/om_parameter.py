# src/om_cli/models/om_parameter.py

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class OMParameterType(Enum):
    STRING = 0
    INTEGER = 1
    BOOLEAN = 2
    UNDEFINED = 3


class OMParameter(BaseModel):
    """
    Represents an OM parameter.

    Attributes:
        name (str): The name of the parameter.
        type (OMParameterType): The type of the parameter.
            - STRING: A string parameter.
            - INTEGER: An integer parameter.
            - BOOLEAN: True or False.
            - UNDEFINED: The type is not defined.
        value (str | None): The current value of the parameter (optional).
        default_value (str | None): The default value of the parameter, will be used if you press enter without entering anything in the prompt (optional).
        preset_value (str | None): The preset value of the parameter, used to set parameter values during the menu definition (optional).
        api_parameter_name (str | None): The name of the parameter to use with an API if not the same as name (optional).
        custom_input_name (str | None): Custom input name for the parameter.
            Used when a static om_parameter name should be read in but the exported parameter name should be different (optional).
        override_parameter_name: (str | None): The internal parameter name to override when a custom output name is required.
            Used when the same action is used multiple times but needs separate parameters
        custom_text (str | None): Custom text for the parameter.
            Used for prompts and other information about the parameter (optional).
        non_stick (bool): True if the parameter is non-stick, False otherwise.
          Non-stick parameters are reset when the action is executed multiple times.
        command_parameter (bool): Decides if the parameter should included when generating the command. Default False. (optional).
        custom_parameter (bool): True if the parameter is a custom parameter, False otherwise.
            Custom parameters are parameters without an Action Pack action parameter definition.
        override_output_parameter_name (bool): True it the parameter is an output parameter and its name should be overridden, False otherwise.
            Used when the parameter name should be overridden but it should not prompt for user input as it would otherwise
            do when a parameter is specified in the OMTree.
        action_index (int | None): The index of the action that the parameter is created during (optional).
    """

    name: str
    type: OMParameterType = OMParameterType.STRING
    value: str | None = None
    default_value: str | None = None
    preset_value: str | None = None
    api_parameter_name: str | None = None
    custom_input_name: str | None = None
    override_parameter_name: str | None = None
    custom_text: str | None = None
    non_stick: bool = False
    command_parameter: bool = False
    custom_parameter: bool = False
    override_output_parameter_name: bool = False
    action_index: int | None = None

    def get_type_string(self) -> str:
        """
        Converts the OM parameter type as a string.

        Returns:
            str: The string representation of the OM parameter type.
        """
        if self.type == OMParameterType.STRING:
            return "String"
        elif self.type == OMParameterType.BOOLEAN:
            return "Boolean"
        elif self.type == OMParameterType.INTEGER:
            return "Integer"
        elif self.type == OMParameterType.UNDEFINED:
            return "Undefined"
        else:
            # logger.warning("Converting the OM parameter type %s is currently not handled", om_parameter_type)
            return str(self.type)
