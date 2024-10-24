# src/om_cli/models/om_condition_group.py

from enum import Enum

from pydantic import BaseModel

from src.om_cli.logger import logger
from src.om_cli.models.om_condition import OMCondition


class OMConditionGroupOperator(Enum):
    AND = 0
    OR = 1


class OMConditionGroup(BaseModel):
    """
    Represents a group of conditions.

    Attributes:
        conditions (list[OMCondition]): The conditions to evaluate.
        operator (OMConditionGroupOperator): The operator to use to evaluate the conditions.
    """

    conditions: list[OMCondition]
    operator: OMConditionGroupOperator = OMConditionGroupOperator.AND

    def evaluate(self, parameters):
        if self.operator == OMConditionGroupOperator.AND:
            result = all(condition.evaluate(parameters) for condition in self.conditions)
            logger.debug(f"ConditionGroup with operator AND evaluated to {result}")
            return result
        elif self.operator == OMConditionGroupOperator.OR:
            result = any(condition.evaluate(parameters) for condition in self.conditions)
            logger.debug(f"ConditionGroup with operator OR evaluated to {result}")
            return result
        logger.debug("ConditionGroup operator not recognized. Returning False")
        return False
