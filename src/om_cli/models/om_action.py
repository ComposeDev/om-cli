# src/om_cli/models/om_action.py

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from src.om_cli.models.om_condition_group import OMConditionGroup
from src.om_cli.models.om_parameter_list import OMParameterList


class OMActionType(Enum):
    API_REQUEST = 0
    FUNCTION_CALL = 1
    LOOP_START = 2
    LOOP_END = 3


class OMAction(BaseModel):
    """
    Represents an OM action.

    Attributes:
        type (OMActionType): The type of the action.
        name (str): The name of the action.
        loop_number (int): The indek of the loop.
        custom_loop_repeat_prompt (str): The custom prompt to display when asking to repeat the loop.
        failure_termination (bool): If set to False, the action will not terminate if the action results in Failure. Large exceptions might still occur Defaults to True.
        parameters (OMParameterList): The parameters to pass to the action.
        skip_if_conditions (list[OMConditionGroup]): The conditions to skip the action.

    TODO:
        - Add support for run_if_conditions
    """

    type: OMActionType
    name: str
    loop_number: int | None = None
    custom_loop_repeat_prompt: str | None = None
    failure_termination: bool = True
    parameters: OMParameterList = OMParameterList()
    skip_if_conditions: list[OMConditionGroup] = []
