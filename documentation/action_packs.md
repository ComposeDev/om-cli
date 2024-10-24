# Action Packs Readme

## Introduction

Action packs are modular components that encapsulate a set of related actions to use in the OM CLI system.
They are designed to be reusable and extendable, allowing you to create custom actions to perform specific tasks.


## Table of Contents

1. [Installation](#installation)
2. [Definition](#definition)
3. [Using an Action Pack](#using-an-action-pack)
4. [Customizing Action Packs](#customizing-action-packs)
5. [Best Practices](#best-practices)

## Installation

Action packs are installed or upgraded by putting the action pack .py-file in the `action_packs` directory.
The OM CLI system will automatically load all action packs in this directory during runtime.

## Definition

An action pack is a collection of actions. Each action is a function that performs a specific task.
For action pack validation during runtime we have a PARAMETER_DEFINITIONS dictionary in each action pack file.

#### Action pack structure

Action packs are defined as Python modules in .py-files with a set of functions that perform specific tasks.
Each function is an action that can be executed by the OM CLI system.

```
[Includes]
[Constant variables]

[PARAMETER_DEFINITIONS]

[Action function definitions]
[Helper function definitions]
```

#### PARAMETER_DEFINITIONS
In the PARAMETER_DEFINITIONS dictionary, you define the parameters that each action in the action pack uses.
Each parameter is defined by a key-value pair where the key is the name of the parameter and the value is a dictionary with the parameter definition.
The validation is done on the following points:
- When an action pack action is loaded it will check the PARAMETER_DEFINITIONS dictionary for the action, if it is not found the validation will fail.
- If a parameter type set in the menu tree is not matching the type in the PARAMETER_DEFINITIONS dictionary, the validation will fail.
- In order to use a non defined parameter in an action in the operation tree, it must have the "custom_parameter" key set to True otherwise the validation will fail.
- TODO: Add required parameters validation. Will require checking previous actions in the operation tree for parameters that are required by the current action.
- TODO: Use the direction key in the PARAMETER_DEFINITIONS dictionary to validate that the parameter is used correctly in the operation tree. For example when using ´override_output_parameter_name´.

##### Example
```json
{
    "print_response": {},
    "print_parameter": {"parameter_value": {"direction": "input", "type": "STRING"}},
    "prompt_for_parameters": {},
    "prompt_for_yes_no": {
        "question": {"direction": "input", "type": "STRING"},
        "user_response_value": {"direction": "output", "type": "BOOLEAN"},
    }
}
```

#### Action function structure

Each action function should follow the structure below:
    
```python
def action_name(result_object, action_parameters, action_index):
    """
    Action description.

    OMParameters used:
        - parameter_name: Description (Type)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        Exception: If an unexpected error occurs while executing the action.

    """
    try:
        # Action code here

        new_parameters = []
        result_object = ResultObject(True, "", None, new_parameters)
    except Exception as ex:
        result_object = ResultObject(False, f"An unexpected error occurred while executing the action: {ex}", None, [])

    return result_object
```

#### Function arguments:
| Argument            | Description                                                                                                                                                                                                                                                |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `result_object`     | The result object from the previous action and the variable to store the result of the current action. It can be used to pass an API response to the next action and to be able to make decisions based on the result without having to parse a parameter. |
| `action_parameters` | Accumulated parameters from previous and the current action in the operation.                                                                                                                                                                              |
| `action_index`      | The index of the current action in the operation. Used to keep track of the current action in the operation and to access the parameters of the current action.                                                                                            |

#### Returns:
| Return value        | Description                                                                                                                |
|---------------------|----------------------------------------------------------------------------------------------------------------------------|
| `ResultObject`      | The updated result object. Should contain the result of the action and any error messages if the action failed.            |


#### Helper functions

Action packs can contain helper functions that are used by multiple actions in the action pack.
These functions should be defined at the bottom of the action pack file and should be prefixed with an underscore to indicate that they are not actions.

#### Common includes

When we want to include an external function directly we must import it using an underscore prefix since otherwise the function will be validated as an action.
    
```python
import json                                                                                        # For parsing JSON
from consolemenu import Screen                                                                     # For prompting the user using console-menu
from rich import print_json as _print_json                                                         # For pretty printing JSON with syntax highlighting
from src.om_cli.models.result_object import ResultObject                                           # For passing on the result object between actions
from src.om_cli.models.om_parameter import OMParameter, OMParameterType                            # For defining and using OMParameters
from src.om_cli.helpers.text_helpers import colorize_text                                          # For colorizing output text
from src.om_cli.logger import logger                                                               # For logging
```

#### Example - Action

Here is an example of how an action pack function is defined:

TODO: Remove the placeholder functionality from the example since it is now incorporated in the base system.
```python
def print_parameter(result_object, action_parameters, action_index):
    """
    Action for printing a parameter.
    Can use placeholders in the parameter_value string to reference other OMParameters.
        Use the format: {{parameter_name}} in the question string and name the OMParameter accordingly.

    OMParameters used:
        - parameter_value: The value of the parameter to print (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no parameter value is found.
        Exception: If an unexpected error occurs while printing the parameter.

    """
    try:
        (found_parameter_value_parameter, parameter_value_parameter) = get_om_parameter("parameter_value", action_parameters, action_index)
        parameter_value = parameter_value_parameter.value if found_parameter_value_parameter else None

        if not parameter_value:
            raise ValueError("Found no parameter value to print")

        # Find all placeholders in the parameter_value
        placeholders = re.findall(r'{{(\w+)}}', parameter_value)

        # Replace placeholders with corresponding OMParameter values
        for placeholder in placeholders:
            (found_param, param) = get_om_parameter(placeholder, action_parameters, action_index)
            if found_param:
                parameter_value = parameter_value.replace(f'{{{{{placeholder}}}}}', str(param.value))

        try:
            # Check if the parameter value is JSON otherwise print the text without JSON color highlighting
            parameter_json_value = json.loads(parameter_value)
            logger.debug("The parameter seems to be of the JSON type")
            print_json(data=parameter_json_value)
        except json.JSONDecodeError as ex:
            logger.debug("The parameter does not seem to be of the JSON type: %s", ex)
            print(colorize_text(f"\n{parameter_value}\n", INFO_COLOR))

        result_object = ResultObject(True, "", None, [])
    except Exception as ex:
        result_object = ResultObject(False, f"An unexpected error occurred while printing the parameter: {ex}", None, [])

    return result_object
```

## Using an Action Pack action

To use an action from an action pack, you need to reference the action in an operation definition.
The action is referenced by its name and the parameters it requires.

#### Individual Action Pack documentation

Each action pack should have its own documentation with a list of available actions and their parameters.
You can find them in the `documentation/action_packs` directory.

#### Example - How to use

Here is an example of how an operation is defined when using the `print_parameter` action from the example above:

```json
{ "operation_id": "print_value", "menu_title": "Print a parameter", "help_text": "This operation will print the value of a parameter.", "actions": [
    { "type": "FUNCTION_CALL", "name": "print_parameter", "parameters": [
        { "name": "parameter_value", "preset_value": "This text will be printed" }
    ] }
}
```

#### Specific functionality

##### Creating a new OMParameter

To create a new OMParameter in an OMAction definition, you use the `OMParameter` class.
To see the available parameter attributes, refer to the [OMParameter documentation](om_tree.md##OMParameter).

When creating a new OMParameter, you should use the `override_internal_action_parameter_name` function to ensure that the parameter name can be overridden.
This is especially useful when you want to use the same action in multiple operations with different parameter names or when same parameter name is used in multiple actions and the value should not be overridden.

You can create multiple OMParameters in an action definition by placing them in a list and passing the list to the result_object when returning from the action.

All OMParameter values wil be stored as strings in the OMParameter object and then converted to the correct type when needed.

###### Example
```python
OMParameter(type=OMParameterType.INTEGER, name=override_internal_action_parameter_name(action_parameters, "new_parameter_name", action_index), value="12345", non_stick=True, action_index=action_index)
```