# OM Tree Setup Documentation
===========================

This document provides a guide on how to set up an Operation Menu using the classes `OMTree`, `OMOperation`, `OMAction`, `OMParameter`, `OMConditionGroup`, and `OMCondition`.

## Table of Contents
1. [Introduction](#introduction)
2. [OMTree](#omtree)
2. [OMOperation](#omoperation)
3. [OMAction](#omaction)
4. [OMParameter](#omparameter)
5. [OMConditionGroup](#omconditiongroup)
6. [OMCondition](#omcondition)
7. [Examples](#examples)

## Introduction
The Operation Menu (OM) tree is a hierarchical structure used to define **operations**, **actions**, and **parameters** using the `OMTree` class.

**Operation**: Represents a menu item in the CLI. Can contain child operations forming submenus or actions to perform.
**Action**: Represents an action to perform in an Operation. An action is either a predefined Python function or an API Request. Actions usually contain parameters.
**Parameter**: Represents a parameter for an action. Used to pass values to and from actions, either as user input or generated values.
**Condition**: Represents a condition that can be used to skip an action based on the value of a parameter.
**ConditionGroup**: Represents a group of conditions that can be used with an AND or OR operator.

## OMTree
`OMTree` is a structure that contains the OM Tree definition.

### Attributes

| Property name              | Value type      | Requirement | Description                                                                                                          |
|----------------------------|-----------------|-------------|----------------------------------------------------------------------------------------------------------------------|
| name                       | string          | Required    | The name of the tree. Shown as the menu header.                                                                      |
| description                | string          | Optional    | The description of the tree. Shown as the menu sub header.                                                           |
| custom_variables           | dict            | Optional    | Custom variables that can be used to replace placeholder variables in the tree. An example is common paths.          |
| operations                 | [OMOperation]   | Required    | List of operations in the tree. Represents the menu hierarchy.                                                       |

### Example
```json
{
    "name": "OM Tree Name", "description": "OM Tree Description",
    "custom_variables": {
        "common_path": "/path/to/common"
    }, "operations": [...]
}

```


## OMOperation
`OMOperation` represents an operation in the OM tree. It can contain child operations and actions.

### Attributes

| Property name              | Value type      | Requirement | Default value | Value alternatives | Description                                                                                                                                                                                                 |
|----------------------------|-----------------|-------------|---------------|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| operation_id               | string          | Required    | N/A           | -                  | A unique internal id for that specific operation.                                                                                                                                                           |
| menu_title                 | string          | Required    | N/A           | -                  | The title presented in the menu.                                                                                                                                                                            |
| help_text                  | string          | Optional    | ""            | -                  | Optional help description if anything more than the auto generated info is needed.                                                                                                                          |
| actions                    | [OMAction]      | Optional    | []            | []                 | List of actions to perform if the menu item does not have children.                                                                                                                                         |
| children                   | [OMOperation]   | Optional    | []            | []                 | Submenu items represented by OMOperations.                                                                                                                                                                  |

### Example 1
```json
{
    "operation_id": "operation_id", "menu_title": "Menu Title", "help_text": "Help Text", "children": [
        { "operation_id": "child_operation_id", "menu_title": "Child Menu Title", "help_text": "Child Help Text", "actions": [...] },
        { "operation_id": "child_operation_id2", "menu_title": "Child Menu Title 2", "help_text": "Child Help Text 2", "actions": [...] }
    ]
}
```

### Example 2
```json
{
    "operation_id": "operation_id", "menu_title": "Menu Title", "help_text": "Help Text", "actions": [
        { "type": "FUNCTION_CALL", "name": "action_name", "parameters": [
                { "name": "parameter_name", "type": "BOOLEAN", "default_value": "True" },
                { "name": "parameter_name2", "type": "INTEGER", "default_value": "10" }
            ]
        }
    ]
}

```

## OMAction
`OMAction` represents an action in the OM tree. It can contain parameters.

### Attributes
| Property name              | Value type      | Requirement | Default value | Value alternatives | Description                                                                                                                                                                                                 |
|----------------------------|-----------------|-------------|---------------|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name                       | string          | Required    | N/A           | -                  | Internal action name. Used for referring to a specific api endpoint or a specific local function.                                                                                                           |
| type                       | OMActionType    | Required    | N/A           | >                  | The type of action to perform.                                                                                                                                                                              |
|                            |                 |             |               | FUNCTION_CALL      | Local predefined function.                                                                                                                                                                                  |
|                            |                 |             |               | API_REQUEST        | External API request.                                                                                                                                                                                       |
|                            |                 |             |               | LOOP_START         | Indicates the start of a specific loop.                                                                                                                                                                     |
|                            |                 |             |               | LOOP_END           | Indicates the end of a specific loop.                                                                                                                                                                       |
| custom_loop_repeat_prompt  | string          | Optional    | None          | -                  | Contains the custom prompt if a custom repeat prompt should be used. Will be used if it is defined otherwise the prompt will be: Do you want to repeat the loop [action.name]?                              |
| failure_termination        | boolean         | Optional    | True          | True / False       | If set to False, the action will not terminate if the action results in Failure. Large exceptions might still occur. Defaults to True.                                                                      |
| loop_number                | Integer         | Optional    | None          | 1+                 | The loop index, in order to have multiple loops and clearly see which one is referenced.                                                                                                                    |
| parameters                 | [OMParameterList] | Optional  | OMParameterList() | -              | Object containing a list of parameters used during the action.                                                                                                                                              |
| skip_if_conditions         | [OMConditionGroup] | Optional | None          | []                 | List of condition groups to determine if an action should be skipped.                                                                                                                                       |

### Example 1
```json
{ "type": "FUNCTION_CALL", "name": "action_name", , "parameters": [
        { "name": "parameter_name", "type": "STRING", "default_value": "Default Value" }
    ] }
```

### Example 2
```json
{ "type": "API_REQUEST", "name": "api_name", "parameters": [
        { "name": "parameter_name", "type": "STRING", "default_value": "Default Value" }
    ] },
```

## OMParameter
`OMParameter` represents a parameter for an action in the OM tree.

### Attributes
| Property name                  | Value type      | Requirement | Default value | Value alternatives | Description                                                                                                                                                                                                 |
|--------------------------------|-----------------|-------------|---------------|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name                           | string          | Required    | N/A           | -                  | Internal parameter name. Used for fetching, using and overriding specific parameters.                                                                                                                       |
| type                           | OMParameterType | Optional    | STRING        | >                  | The type of parameter. The value provided to the parameter will be validated against the type. STRING if not specified.                                                                                     |
|                                |                 |             |               | STRING             | String value.                                                                                                                                                                                               |
|                                |                 |             |               | INTEGER            | May not be empty if it does not have a default value.                                                                                                                                                       |
|                                |                 |             |               | BOOLEAN            | Can be true/True or false/False.                                                                                                                                                                            |
|                                |                 |             |               | AUTO               | A parameter with an automatic process for defining its value. The value cannot be altered by the user.                                                                                                      |
|                                |                 |             |               | UNDEFINED          | Used to indicate that the parameter type is not defined.                                                                                                                                                    |
| value                          |                 | Optional    | None          | -                  | The assigned value of the parameter.                                                                                                                                                                        |
| default_value                  |                 | Optional    | None          | -                  | The value that will be assigned automatically if the user does not enter a value during a parameter prompt. Will present the default value during the prompt.                                               |
| preset_value                   |                 | Optional    | None          | -                  | If a value should be preset without the user getting prompted for it. Can be overridden during a repeated loop if the non_stick property is set to True. TODO: Verify                                       |
| api_parameter_name             | string          | Optional    | None          | -                  | The api parameter name if not the same as the name.                                                                                                                                                         |
| custom_input_name              | string          | Optional    | None          | -                  | Custom input name for the parameter. Used when a static parameter name should be read but the exported parameter name should be different.                                                                  |
| override_parameter_name        | string          | Optional    | None          | -                  | The internal parameter name to override when a custom output name is required. Used when the same action is used multiple times but needs separate parameters.                                              |
| custom_text                    | string          | Optional    | None          | -                  | Custom text used for prompts.                                                                                                                                                                               |
| non_stick                      | boolean         | Optional    | FALSE         | True / False       | Decides if a parameter should be prompting for a new input value when repeating an action.                                                                                                                  |
| command_parameter              | boolean         | Optional    | FALSE         | True / False       | Decides if the parameter should included when generating the command.                                                                                                                                       |
| custom_parameter               | boolean         | Optional    | FALSE         | True / False       | Custom parameters are parameters without an Action Pack action parameter definition. Can be used when creating a custom prompt.                                                                             |
| override_output_parameter_name | boolean         | Optional    | FALSE         | True / False       | Since output parameters should not promt for user input before the action is run we have to indicate that this is an override_output_parameter_name if we have the parameter in the OMTree.                 |
| action_index                   | integer         | N/A         | None          | -                  | Internal index to keep track of which action the parameter is based from.                                                                                                                                   |

### Example
TODO: Add more examples
```json
{ "name": "other_parameter_name", "custom_input_name": "other_name", "override_output_parameter_name": "parameter_name", "type": "STRING", "default_value": "Default Value" }
```

## OMConditionGroup
`OMConditionGroup` represents a group of conditions in the OM tree.

### Attributes
| Property name              | Value type               | Requirement | Default value | Value alternatives | Description                                                                                              |
|----------------------------|--------------------------|-------------|---------------|--------------------|----------------------------------------------------------------------------------------------------------|
| operator                   | OMConditionGroupOperator | Optional    | AND           | >                  | The operator for combining conditions.                                                                   |
|                            |                          |             |               | AND                | All conditions must be true.                                                                             |
|                            |                          |             |               | OR                 | At least one condition must be true.                                                                     |
| conditions                 | list[OMCondition]        | Required    | []            | []                 | List of conditions in the group.                                                                         |

### Example
```json
{
    "operator": "AND", "conditions": [
        { "parameter": "parameter_name", "operator": "==", "value": "Value" }
    ]
}
```

## OMCondition

`OMCondition` represents a condition in the OM tree.

Determines if an action should be skipped based on the value of a parameter.
If the condition is met, the action will be skipped.


### Attributes
| Property name              | Value type      | Requirement | Default value | Value alternatives  | Description                                                                                              |
|----------------------------|-----------------|-------------|---------------|---------------------|----------------------------------------------------------------------------------------------------------|
| parameter_name             | string          | Required    | N/A           | -                   | The name of the parameter to compare.                                                                    |
| jsonpath                   | string          | Required    | None          | -                   | The JSON path to extract the value from the result object. Uses dot-walking. '$' for the object base.    |
| regex                      | string          | Required    | None          | -                   | The regex to compare the extracted value with.                                                           |
| skip_if_path_not_found     | boolean | None  | Optional    | None          | True / False / None | If the action should be skipped if the path is not found.                                                |

### Example
```json
{ "parameten_name": "parameter_name", "jsonpath": "$", "regex": "^find this string$", "skip_if_path_not_found": true }
```

## Examples
### Example 1: Creating an Operation with Actions and Parameters
```json
{
    "operation_id": "operation_id", "menu_title": "Menu Title", "help_text": "Help Text", "actions": [
        { "type": "FUNCTION_CALL", "name": "action_name", "parameters": [
                { "name": "Parameter Name", "default_value": "Default Value" }
            ]
        }
    ]
}
```

### Example 2: Creating an Operation with Conditions
```json
{
    "operation_id": "operation_id", "menu_title": "Menu Title", "help_text": "Help Text", "actions": [
        { "type": "FUNCTION_CALL", "name": "action_name", "skip_if_conditions": [
            { "conditions": [
                { "parameten_name": "parameter_name", "jsonpath": "$", "regex": "^find this string$", "skip_if_path_not_found": true }
            }
        }
    ]
}
```

### Example 3: Creating an Operation with Child Operations
```json
{
    "operation_id": "operation_id", "menu_title": "Menu Title", "help_text": "Help Text", "children": [
        { "operation_id": "child_operation_id", "menu_title": "Child Menu Title", "help_text": "Child Help Text" },
        { "operation_id": "child_operation_id2", "menu_title": "Child Menu Title 2", "help_text": "Child Help Text 2" }
    ]
}
```

### Example 4: Creating an Operation with actions using the same action parameter name in multiple actions with override_parameter_name and custom_input_name
TODO: Verify this example
We have an action with two parameters, `internal_action_parameter_name1` and `internal_action_parameter_name2`.
If we want to use the same parameter name in multiple actions in the same operation, we can use `override_parameter_name` and `custom_input_name` to achieve this.

In `override_parameter_name`, we specify the internal action parameter name that we want to override.
In `name`, we specify the new custom parameter name that we want to use.
Since the internal action parameter names are named for matching with some actions that chain well together, we can use `custom_input_name` to specify which parameter name it should use as input.
This way, we can use the same parameter name in multiple actions without owerwriting the values of the parameters in the actions.
So in the example below, the `new_custom_parameter_name_cat` will use the value of `new_custom_parameter_name_dog` as input.
```json

{
    "operation_id": "operation_id", "menu_title": "Menu Title", "help_text": "Help Text", "actions": [
        { "type": "FUNCTION_CALL", "name": "action_name1", "parameters": [
                { "name": "new_custom_parameter_name_dog", "override_parameter_name": "internal_action_parameter_name1" },
                { "name": "new_custom_parameter_name_cat", "override_parameter_name": "internal_action_parameter_name2", "custom_input_name": "new_custom_parameter_name_dog" }
            ]
        },
        { "type": "FUNCTION_CALL", "name": "action_name2", "parameters": [
                { "name": "new_custom_parameter_name_owl", "override_parameter_name": "internal_action_parameter_name1" },
                { "name": "new_custom_parameter_name_rabbit", "override_parameter_name": "internal_action_parameter_name2", "custom_input_name": "new_custom_parameter_name_owl" }
            ]
        }
    ]
}
```

### Example 5: Creating an Operation with Actions, Parameters, and Conditions
```json
{
    "operation_id": "operation_id", "menu_title": "Menu Title", "help_text": "Help Text", "actions": [
        { "type": "FUNCTION_CALL", "name": "action_name1", "parameters": [
                { "name": "Parameter Name", "default_value": "Default Value" }
            ], "skip_if_conditions": [
                { "conditions": [
                    { "parameten_name": "parameter_name", "jsonpath": "$", "regex": "^find this string$", "skip_if_path_not_found": true }
                ]
            }
        }
    ]
}
```

TODO: Add more useful examples and replace the old ones