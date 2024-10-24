# src/om_cli/models/result_object.py
from typing import Optional

from requests import Response

from src.om_cli.models.om_parameter_list import OMParameterList


class ResultObject:
    """
    Represents the result of an action.

    Attributes:
        success (bool): Indicates whether the action was successful.
        text (str): Additional text describing the result.
        response (Response): The response object associated with the result.
        parameters (dict): Additional parameters related to the result.
        repeat_action (bool): Indicates whether the action should prompt be repeated.
        repeat_loop (bool | None): Indicates whether the loop should be repeated.
    """

    def __init__(
        self,
        success: bool,
        text: Optional[str] = None,
        response: Response = None,
        parameters: Optional[OMParameterList] = None,
        repeat_action: bool = False,
        repeat_loop: bool | None = None,
    ):
        self.success = success
        self.text = text
        self.response = response
        self.parameters = parameters or OMParameterList()
        self.repeat_action = repeat_action
        self.repeat_loop = repeat_loop

    success: bool = False
    text: Optional[str] = None
    response: Response = None
    parameters: OMParameterList = OMParameterList()
    repeat_action: bool = False
    repeat_loop: bool | None = None
