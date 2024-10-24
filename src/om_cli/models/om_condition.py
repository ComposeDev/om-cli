# src/om_cli/models/om_condition.py

from __future__ import annotations

import json
import re

import jsonpath_ng
from pydantic import BaseModel

from src.om_cli.logger import logger


class OMCondition(BaseModel):
    """
    Represents an OM condition.

    Attributes:
        parameter_name (str): The name of the parameter to compare.
        jsonpath (str): The JSON path to extract the value from the result object.
        regex (str): The regex to compare the extracted value with.
        skip_if_path_not_found (bool): If the action should be skipped if the path is not found.

    TODO: Should skip_if_path_not_found be a pure boolean?
    """

    parameter_name: str
    jsonpath: str
    regex: str
    skip_if_path_not_found: bool | None = None

    def evaluate(self, om_parameters):
        (found_om_parameter, om_parameter) = om_parameters.get_om_parameter(self.parameter_name, -1)

        matches = []
        if found_om_parameter:
            value = om_parameter.value
            try:
                value = json.loads(value)
            except json.JSONDecodeError as e:
                logger.debug(
                    f"Unable to to decode parameter value as JSON for {self.parameter_name} | Could be expected: {e}"
                )

            json_expr = jsonpath_ng.parse(self.jsonpath)
            matches = json_expr.find(value)

        if not matches:
            result = self.skip_if_path_not_found
            logger.debug(
                f"Condition {self.parameter_name} with jsonpath {self.jsonpath} not found. Returning {result}"
            )
            return result

        for match in matches:
            if re.search(self.regex, str(match.value)):
                logger.debug(
                    f"Condition {self.parameter_name} with jsonpath {self.jsonpath} and regex {self.regex} matched value {match.value}. Returning True"
                )
                return True
        logger.debug(
            f"Condition {self.parameter_name} with jsonpath {self.jsonpath} and regex {self.regex} did not match any value. Returning False"
        )
        return False
