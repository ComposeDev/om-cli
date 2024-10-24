# src/om_cli/models/om_tree.py

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from src.om_cli.models.om_operation import OMOperation


class OMTree(BaseModel):
    """
    Represents an OM tree.

    Attributes:
        name (str): The name of the tree.
        description (str): The description of the tree.
        custom_variables (dict): The custom variables of the tree. Used to replace placeholder variables in the tree. An example is common paths.
        operations (List[OMOperation]): The operations in the tree.
    """

    name: str
    description: str
    custom_variables: dict
    operations: List[OMOperation]
