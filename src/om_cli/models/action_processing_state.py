# src/om_cli/models/action_processing_state.py

from src.om_cli.models.loop_state import LoopState
from src.om_cli.models.om_parameter_list import OMParameterList


class OperationProcessingState:
    """
    Represents the state of the action processing.

    Attributes:
        loop_state (LoopState): The state of the loop.
        extra_parameters (OMParameterList): The extra parameters to pass to the action.
        parameter_history (OMParameterList): The history of the parameters.
        api_result_history (list): The history of the API results.
        action_history (set): The history of the actions.
        custom_components (CustomComponents): The custom components.
        api_handler (APIHandler): The API handler.

    """

    def __init__(self, custom_components, api_handler):
        self.loop_state = LoopState()
        self.extra_parameters = OMParameterList()
        self.parameter_history = OMParameterList()
        self.api_result_history = []
        self.action_history = set()
        self.custom_components = custom_components
        self.api_handler = api_handler

    def get_custom_components(self):
        return self.custom_components

    def get_api_handler(self):
        return self.api_handler

    def add_extra_parameter(self, parameter):
        self.extra_parameters.add_parameter(parameter)

    def add_to_parameter_history(self, parameters):
        self.parameter_history.add_parameter(parameters)

    def add_to_api_result_history(self, result):
        self.api_result_history.append(result)

    def add_to_action_history(self, action_name):
        self.action_history.add(action_name)

    def is_action_repeated(self, action_name):
        return action_name in self.action_history
