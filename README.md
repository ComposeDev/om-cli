# OM CLI Framework

## Table of Contents
1. [Introduction](#introduction)
2. [Appendix](#appendix)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Commands](#commands)
7. [Basic flow](#basic-flow)
8. [License](#license)

## Disclaimer
The OM CLI documentation is in an early stage and is prone to change.

## Introduction
The OM CLI (Operation Menu Command Line Interface) is a terminal-based framework designed to provide a user-friendly, menu-driven interface for executing various Operations, such as API calls.  
It allows users to interface with different systems and present information in a way that suits their needs.  
The menu structure and the Operations are defined using configuration files, making it highly customizable.

![A basic example of the OM CLI](documentation/menu_example1.png)

## Appendix
| Term | Description |
|---|---|
| OM CLI | Operation Menu Command Line Interface. |
| Operation Tree / OMTree | The structure of the menu system, containing Operations and sub-menus. |
| Operation / OMOperation | A menu item in the system, containing either a sub-menu or Actions. |
| Action / OMAction | A function that can be executed, such as an API call or a system command. |
| Parameter / OMParameter | A value that can be used as input or output for an action. |
| Condition / OMCondition | A condition that can be used to control the flow of the framework. |
| API Definition | A configuration file defining the API endpoints and their parameters. |
| Action Pack | A collection of Action functions that can be loaded into the framework, extending the available Actions. |

## Installation
Clone the project and install the required dependencies.

```bash
git clone https://github.com/ComposeDev/om-cli
cd om-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x run_cli*
```

### Test Usage
```bash
./run_cli_test.sh
```

## Configuration
The OM CLI framework uses multiple configuration files to define the Operations and API endpoints that can be executed.
It can also load Action Packs to extend the available actions.

### Operation tree configuration
Information on how to configure the Operation Tree can be found [here](documentation/om_tree.md).

### API definitions
Information on how to configure API definitions can be found [here](documentation/api_definitions.md).

### Action Packs
Information on how to use Action Packs can be found [here](documentation/action_packs.md).

## Commands
The OM CLI can be used in two ways: Interactive mode and by argument-based command execution.

It supports the following arguments to control the behavior of the framework.
 - **-l** or **--log_level**:
    Set the log level of the framework.
    Possible values are **DEBUG**, **INFO**, **WARNING**, **ERROR**, **CRITICAL**.
    Default is **INFO**.
 - **-c** or **--custom_path**:
    The path to the custom configuration directory.
    Used when you want to load the custom configuration from a non-default path.
 - **-t** or **--tree_path**: 
    The path to the OMTree configuration file.
    Used when you want to load the OMTree configuration from a non-default path.
 - **-m** or **--mock_api_responses_file_path**:
      The path to the file containing mock API responses.
      Used when you want to load mock API responses instead of using a real API.
      Mostly used for testing and debugging.
 - **-s** or **--skip_looping**:
    Skip the looping behavior of the framework.
    This is useful when running the OM CLI in the argument-based command execution mode.
 - **-g** or **--generate_tree**:
    Generate a new OMTree configuration file from the current OMTree.
    Used when debugging and want to reconstruct the OMTree configuration file.
 - **-o** or **--operation**:
    Execute an Operation directly from the command line.
    Example: `om_cli -o operation_name`
 - **\*params**:
    Provide params/arguments for the command to be executed.
    If an argument does not begin with a dash, it is considered a param for the command.
    If the argument value is a string, it should be enclosed in double quotes.
    All arguments should be provided in the format `param_name=value`.
    Example: `om_cli -o operation_name param1=value1 param2="value2"`
    Example2: `om_cli -o operation_name param1=value1 param2="value2" -l DEBUG`

### Interactive mode
When using the interactive mode, the user is presented with a menu-driven interface that allows them to navigate through the Operation Tree and execute commands.

### Argument based command execution
This mode is made for executing Operations directly from the command line, without having to navigate through the menu.
It is accessed by providing the Operation and its Parameters as arguments when starting the OM CLI.

## Basic flow
### Interactive mode:

1. Start the OM CLI
2. Validate and load the configuration files
3. Display the main menu
4. The user selects an Operation or submenu
6. If the Operation has items in the Children list, display the submenu
7. If the Operation has items in the Actions list, start executing the Actions
9. If an Action uses input Parameters, prompt the user for input or use previous Parameter values
10. Process the Action function
11. The Action might generate output Parameters
12. When all actions have been executed, display the final result with a generated command for repeating the Operation without the need for using the interactive mode
13. Return to the main menu

### Argument based command execution:

1. Start the OM CLI using the -o/--operation argument and usually the -s/--skip_looping argument
2. Validate and load the configuration files
3. Find the Operation with the provided name
4. Verify the provided arguments against the Operation's Parameters
5. Execute the Operation's Actions
6. Process the Action function
7. The Action might generate output Parameters
8. When all Actions have been executed and the Operation is completed, display the final result
9. Exit

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

This project includes third-party dependencies with the following licenses:
- Apache Software License [Apache-2.0](LICENSES/APACHE_LICENSE.txt)
- Mozilla Public License [MPL-2.0](LICENSES/MPL_LICENSE.txt)

See the [LICENSES](LICENSES) directory for details.