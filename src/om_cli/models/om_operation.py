# src/om_cli/models/om_operation.py

from __future__ import annotations

from pydantic import BaseModel

from src.om_cli.models.om_action import OMAction


class OMOperation(BaseModel):
    """
    Represents an OM operation.

    Attributes:
        operation_id (str): The ID of the operation.
        menu_title (str): The title of the operation in the menu.
        help_text (str): The help text for the operation.
        actions (list[OMAction] | None): The list of actions associated with the operation (optional).
        children (list[OMOperation] | None): The list of child operations (optional).
    """

    operation_id: str
    menu_title: str
    help_text: str = "This is a sample help text"
    actions: list[OMAction] = []
    children: list[OMOperation] = []
