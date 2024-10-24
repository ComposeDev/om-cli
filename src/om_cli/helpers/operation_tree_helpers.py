# src/om_cli/helpers/operation_tree_helpers.py

import copy

from src.om_cli.models.om_operation import OMOperation


def get_operation_by_id(operations: list[OMOperation], operation_id: str) -> OMOperation:
    """
    Retrieves an operation by its operation_id.

    Args:
        operations (list): The operations list to search in.
        operation_id (str): The operation_id to search for.

    Requires to make a deep copy of the operation to avoid modifying the original operation which might otherwise
    cause unexpected behavior if the same operation is used again during the session.
    """

    operation = get_operation_by_id_nested(operations, operation_id)
    if operation:
        return copy.deepcopy(operation)
    else:
        raise ValueError(f"Operation with id {operation_id} not found")


def get_operation_by_id_nested(
    operations: list[OMOperation], operation_id: str
) -> OMOperation | None:
    """
    Retrieves an operation by its operation_id.

    Args:
        operations (list): The operations list to search in.
        operation_id (str): The operation_id to search for.

    Returns:
        OMOperation: The operation with the given operation_id or None if not found.
    """
    for operation in operations:
        if operation.operation_id == operation_id:
            return operation
        if operation.children:
            if nested_operation := get_operation_by_id_nested(operation.children, operation_id):
                return nested_operation
    return None
