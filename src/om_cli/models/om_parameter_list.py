# src/om_cli/models/om_parameter_list.py

import copy
from typing import List, Optional

from pydantic import BaseModel, Field

from src.om_cli.models.om_parameter import OMParameter, OMParameterType


class OMParameterList(BaseModel):
    Parameters: List[OMParameter] = Field(default_factory=list)

    def __iter__(self):
        """Return an iterator over the parameters."""
        return iter(self.Parameters)

    def __extend__(self, parameters: "OMParameterList"):
        """Extend the parameter list with the given list of parameters."""
        self.Parameters.extend(parameters)

    def __len__(self):
        """Return the number of parameters in the list."""
        return len(self.Parameters)

    def __getitem__(self, index):
        return self.Parameters[index]

    def copy(self):
        """Return a deep copy of the parameter list."""
        return copy.deepcopy(self)

    def has_items(self):
        """Return True if the parameter list has items, otherwise False."""
        return len(self.Parameters) > 0

    def merge(self, other_list: "OMParameterList"):
        """Merge the given parameter list with the current parameter list."""
        if not isinstance(other_list, self.__class__):
            raise TypeError("Expected an instance of OMParameterList")

        for item in other_list:
            found = False
            for i, existing_item in enumerate(self):
                if existing_item.name == item.name:
                    self.Parameters[i] = item
                    found = True
                    break
            if not found:
                self.add_parameter(item)

    def add_parameter(self, parameter: OMParameter):
        """
        Add a parameter to the parameter list.

        Args:
            parameter (OMParameter): The parameter to add.
        """
        self.Parameters.append(parameter)

    def generate_new_base_parameter(
        self,
        name: str,
        action_index: int,
        parameter_type: Optional[OMParameterType] = None,
    ):
        """
        Generate a new base parameter with the specified name and the defauld type of STRING.

        Args:
            name (str): The name of the parameter to generate.
            action_index (int): The current action index.

        Returns:
            OMParameter: The generated OM parameter.
        """
        if parameter_type is None:
            parameter_type = OMParameterType.STRING
        return OMParameter(name=name, type=parameter_type, action_index=action_index)

    def get_om_parameter(self, name: str, action_index: int):
        """
        Get the OM parameter with the specified name from the given list of OM parameters.

        Args:
            name (str): The name of the OM parameter to retrieve.
            action_index (int): The current action index.

        Returns:
            tuple: A tuple containing a boolean value indicating whether the parameter was found,
                and the OM parameter object if found, or None if not found.
        """
        om_parameter_name = self.override_internal_action_parameter_name(name, action_index)

        om_parameter = next(
            (
                om_parameter
                for om_parameter in self.Parameters
                if om_parameter.name == om_parameter_name
            ),
            None,
        )
        return (om_parameter is not None, om_parameter)

    def override_internal_action_parameter_name(
        self, internal_action_parameter_name, current_action_index
    ):
        """
        Overrides the internal action parameter name with custom names.

        Args:
            internal_action_parameter_name (str): The internal action parameter name to override.
            current_action_index (int): The current action index.

        Returns:
            str: The potentially overridden internal action parameter name otherwise the original name.
        """

        if current_action_index is None:
            return internal_action_parameter_name

        return next(
            (
                parameter.name
                for parameter in self.Parameters
                if parameter.override_parameter_name
                and parameter.override_parameter_name == internal_action_parameter_name
                and parameter.action_index == current_action_index
            ),
            internal_action_parameter_name,
        )
