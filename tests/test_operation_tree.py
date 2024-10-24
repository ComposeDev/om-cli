# tests/test_operation_tree.py

import unittest
from typing import List

from src.om_cli.models.om_action import OMAction, OMActionType
from src.om_cli.models.om_operation import OMOperation
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.services.operation_tree_generator import load_om_tree_from_json_file


class TestOperationTree(unittest.TestCase):
    om_tree = load_om_tree_from_json_file("custom/operation_menus/om_tree.json")

    def _test_operation_tree_nesting(self, operations: List[OMOperation]):
        for operation in operations:
            self._assert_operation_attributes(operation)

            if operation.actions:
                self._test_all_actions_have_required_attributes(operation.actions)

            if operation.children:
                self._test_operation_tree_nesting(operation.children)

    def _test_all_actions_have_required_attributes(self, actions: List[OMAction]):
        for action in actions:
            self.assertIsNotNone(action.type)
            self.assertIsNotNone(action.name)

            if action.parameters.has_items():
                self._test_all_action_parameters_have_required_attributes(action.parameters)

    def _test_all_action_parameters_have_required_attributes(self, parameters: OMParameterList):
        for parameter in parameters:
            self.assertIsNotNone(parameter.name)
            self.assertIsNotNone(parameter.type)

    def _assert_operation_attributes(self, operation):
        self.assertIsNotNone(operation.operation_id)
        self.assertGreater(len(operation.operation_id), 0)
        self.assertIsNotNone(operation.menu_title)
        self.assertGreater(len(operation.menu_title), 0)
        self.assertIsNotNone(operation.help_text)
        self.assertGreater(len(operation.help_text), 0)

    def test_om_tree_having_all_required_attributes(self):
        self.assertIsNotNone(self.om_tree.name)
        self.assertGreater(len(self.om_tree.name), 0)
        self.assertIsNotNone(self.om_tree.description)
        self.assertGreater(len(self.om_tree.description), 0)
        self.assertIsNotNone(self.om_tree.custom_variables)
        self.assertIsNotNone(self.om_tree.operations)
        self.assertGreater(len(self.om_tree.operations), 0)

        self._test_operation_tree_nesting(self.om_tree.operations)

    def test_all_operations_loop_completion_order_and_nesting(self):
        # Test that all loop start X have a corresponding loop end X
        # Test that all loop end X comes before its corresponding loop start X
        # Test that all loop end X matches the last loop start X, that is, they start and end in the same loop level
        self._test_operation_tree_nesting_loops(self.om_tree.operations)

    def _test_operation_tree_nesting_loops(self, operation_tree: List[OMOperation]):
        for operation in operation_tree:
            if operation.actions:
                loop_starts = [
                    action for action in operation.actions if action.type == OMActionType.LOOP_START
                ]
                loop_ends = [
                    action for action in operation.actions if action.type == OMActionType.LOOP_END
                ]

                # Ensure loop start X comes before loop end X
                for loop_start in loop_starts:
                    matching_loop_end = next(
                        (
                            action
                            for action in loop_ends
                            if action.loop_number == loop_start.loop_number
                        ),
                        None,
                    )
                    self.assertIsNotNone(
                        matching_loop_end,
                        f"No matching loop end for loop start {loop_start.loop_number}",
                    )
                    if matching_loop_end is not None:
                        self.assertLess(
                            operation.actions.index(loop_start),
                            operation.actions.index(matching_loop_end),
                            f"Loop start {loop_start.loop_number} does not come before Loop end {matching_loop_end.loop_number}",
                        )

                # Ensure nested loops are properly contained
                loop_stack = []
                for action in operation.actions:
                    if action.type == OMActionType.LOOP_START:
                        loop_stack.append(action)
                    elif action.type == OMActionType.LOOP_END:
                        if loop_stack:
                            last_loop_start = loop_stack.pop()
                            self.assertEqual(
                                action.loop_number,
                                last_loop_start.loop_number,
                                f"Loop start {action.loop_number} does not match the last {last_loop_start.loop_number}",
                            )

            if operation.children:
                self._test_operation_tree_nesting_loops(operation.children)


if __name__ == "__main__":
    unittest.main()
