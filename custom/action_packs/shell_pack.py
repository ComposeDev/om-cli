# custom/action_packs/shell_pack.py
import shlex
import subprocess

from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject

PARAMETER_DEFINITIONS = {
    "perform_bash_command": {
        "command": {"direction": "input", "type": "STRING"},
        "use_shell": {"direction": "input", "type": "BOOLEAN"},
        "use_check": {"direction": "input", "type": "BOOLEAN"},
        "print_output": {"direction": "input", "type": "BOOLEAN"},
    }
}


def perform_bash_command(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for performing a bash command.
    Can use placeholders in the command string to reference other OMParameters.
        Use the format: {{parameter_name}} in the command string and name the OMParameter accordingly.

    OMParameters used:
        - command: The bash command to execute (Read)
        - use_shell: If the command should be executed in a shell, defaults to: False (Read)
        - use_check: If the command should be checked for errors, defaults to: True (Read)
            Will raise a CalledProcessError if the command returns a non-zero exit code.
        - print_output: If the command output (stderr, stdout) should be printed in the terminal, defaults to: False (Read)

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If no command is found.
        Exception: If an unexpected error occurs while executing the command.
    """

    def extract_parameter(name: str, default=None) -> str:
        found, parameter = action_parameters.get_om_parameter(name, action_index)
        return parameter.value if found else default

    try:
        command = extract_parameter("command")
        use_shell = extract_parameter("use_shell", "False").lower() == "true"
        use_check = extract_parameter("use_check", "True").lower() == "true"
        print_output = extract_parameter("print_output", "False").lower() == "true"

        if not command:
            raise ValueError("No command found")

        args = command if use_shell else shlex.split(command)
        subprocess_result = subprocess.run(
            args=args,
            shell=use_shell,
            check=use_check,
            capture_output=print_output,
            text=print_output,
        )

        if print_output:
            print("stdout:", subprocess_result.stdout + "\n")
            print("stderr:", subprocess_result.stderr + "\n")

        result_object = ResultObject(
            True, f"Executed the command: {command}", None, OMParameterList()
        )
    except subprocess.CalledProcessError as ex:
        result_object = ResultObject(
            False, f"Failed to execute the command: {ex}", None, OMParameterList()
        )
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while executing the command: {ex}",
            None,
            OMParameterList(),
        )

    return result_object
