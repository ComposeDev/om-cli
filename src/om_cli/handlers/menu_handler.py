# src/om_cli/handlers/menu_handler.py
from consolemenu import ConsoleMenu, MenuFormatBuilder
from consolemenu.format import MenuBorderStyleType
from consolemenu.items import FunctionItem, MenuItem, SubmenuItem
from consolemenu.menu_component import Dimension

from src.om_cli.helpers.text_helpers import colorize_text
from src.om_cli.models.om_operation import OMOperation
from src.om_cli.models.om_parameter import OMParameterType
from src.om_cli.services.custom_components_processing import CustomComponents
from src.om_cli.services.operation_processing import process_operation

SUB_MENU_COLOR = "orange"
ACTION_COLOR = "green"
MISSING_TYPE_COLOR = "red"
HELP_HEADER_COLOR = "orange"
HELP_TITLE_COLOR = "orange"
HELP_TEXT_COLOR = "brown"
HELP_ACTION_TEXT_COLOR = "turquoise"
HELP_PARAMETER_TEXT_COLOR = "pink"
HELP_TOGGLE_COLOR = "yellow"

CUSTOM_COMPONENTS = None

"""
TODO: Fix static skip_looping value
"""


def run_menu(custom_components: CustomComponents):
    """
    Runs the menu based on the provided operation tree.

    Parameters:
    - operation_tree (dict): The operation tree representing the menu structure.

    Returns:
    - None
    """
    global CUSTOM_COMPONENTS
    CUSTOM_COMPONENTS = custom_components
    om_tree = custom_components.get_om_tree()

    menu = create_menu_from_operation_tree(
        om_tree.operations,
        title=om_tree.name,
        subtitle=om_tree.description,
        is_main_menu=True,
    )
    menu.show()


def create_menu_item(operation: OMOperation):
    """
    Create a menu item based on the given operation.

    Args:
        operation: An instance of the Operation class representing the menu operation.

    Returns:
        A menu item object based on the type of operation:
        - If the operation has children, a SubmenuItem object is returned.
        - If the operation has an endpoint name, a FunctionItem object is returned.
        - Otherwise, a MenuItem object is returned.
    """
    if operation.children:
        submenu = create_menu_from_operation_tree(operation.children, title=operation.menu_title)
        return SubmenuItem(colorize_text(operation.menu_title, SUB_MENU_COLOR), submenu)
    if operation.actions:
        return FunctionItem(
            colorize_text(operation.menu_title, ACTION_COLOR),
            process_operation,
            args=[operation, [], CUSTOM_COMPONENTS, False],
        )
    return MenuItem(colorize_text(operation.menu_title, MISSING_TYPE_COLOR))


def create_menu_from_operation_tree(
    operation_tree: list,
    title: str = "Operation Menu CLI",
    subtitle: str = "OM CLI",
    is_main_menu: bool = False,
) -> ConsoleMenu:
    """
    Recursively create a console menu from an operation tree.

    Args:
        operation_tree (list): A list of operations to be added to the menu.
        title (str): The title of the menu.
        subtitle (str): The subtitle of the menu.
        is_main_menu (bool, optional): Specifies whether the menu is the main menu or a sub-menu.
            Defaults to False.

    Returns:
        ConsoleMenu: The created console menu.
    """
    menu_format = (
        MenuFormatBuilder(max_dimension=Dimension(width=120, height=40))
        .set_border_style_type(MenuBorderStyleType.DOUBLE_LINE_OUTER_LIGHT_INNER_BORDER)
        .set_prompt(">>")
        .set_title_align("center")
        .set_subtitle_align("center")
        .set_left_margin(4)
        .set_right_margin(4)
        .show_header_bottom_border(True)
    )

    exit_option_text = "Exit" if is_main_menu else "Back"
    exit_menu_char = "q" if is_main_menu else "b"

    help_text = generate_help_text(operation_tree)

    # The main menu root
    menu = ConsoleMenu(
        title,
        subtitle,
        formatter=menu_format,
        exit_menu_char=exit_menu_char,
        exit_option_text=exit_option_text,
    )

    for operation in operation_tree:
        if menu_item := create_menu_item(operation):
            menu.append_item(menu_item)

    toggle_help_text_item = FunctionItem(
        colorize_text("Toggle help text", HELP_TOGGLE_COLOR),
        toggle_help_text,
        args=[menu, help_text],
        menu_char="0",
    )
    menu.append_item(toggle_help_text_item)

    return menu


def generate_help_text(operation_tree: list) -> str:
    """
    Generates help text for the menu based on the operation tree.

    Args:
        operation_tree (list): A list of operations.

    Returns:
        str: The generated help text.
    """
    help_text = colorize_text("HELP TEXT", HELP_HEADER_COLOR)
    for operation in operation_tree:
        if operation.help_text:
            help_text += (
                "\n.\n"
                + colorize_text(operation.menu_title, HELP_TITLE_COLOR)
                + " - "
                + colorize_text(operation.help_text, HELP_TEXT_COLOR)
                + generate_parameter_help_text(operation)
            )

    help_text += "\n.\n"
    help_text += colorize_text(
        "You can at any time during an Operation use Ctrl+D to abort and return to the main menu.",
        HELP_TOGGLE_COLOR,
    )
    return help_text


def generate_parameter_help_text(operation: OMOperation) -> str:
    """
    Generates help text for all input parameters from the actions in the operation.

    Args:
        operation (Operation): The operation object.

    Returns:
        str: The generated help text.

    TODO: Update this with the new features.
    """
    if not operation.actions:
        return "\n--No required parameters."

    help_text = "\n--Actions with required parameters:"
    for action in operation.actions:
        parameters = [
            f"\n * {parameter.name} ({parameter.get_type_string()})"
            + (" - Is Command Parameter" if parameter.command_parameter else "")
            + (" - Is Non-stick" if parameter.non_stick else "")
            for parameter in action.parameters
            if parameter.type != OMParameterType.AUTO
        ]
        if parameters:
            help_text += colorize_text(
                f"\n -{action.name}:", HELP_ACTION_TEXT_COLOR
            ) + colorize_text("".join(parameters), HELP_PARAMETER_TEXT_COLOR)

    return (
        help_text
        if help_text != "\n--Actions with required parameters:"
        else "\n--No required parameters."
    )


def toggle_help_text(menu: ConsoleMenu, help_text: str = ""):
    """
    Toggles the help text in the menu.

    Args:
        menu (Menu): The menu object.
        help_text (str, optional): The help text to be displayed. Defaults to None.
    """
    menu.epilogue_text = "" if menu.epilogue_text else help_text
    menu.formatter.show_item_bottom_border(menu.exit_item.text, menu.epilogue_text != "")
