# src/om_cli/models/loop_state.py


class LoopState:
    """
    Represents the state of the loop.

    Attributes:
        loop_starts (dict[int, int]): The start index of the loop.
        loop_stack (list[int]): The stack of loop numbers.
        action_index (int): The index of the action

    """

    def __init__(self):
        self.loop_starts: dict = {}
        self.loop_stack: list = []
        self.action_index: int = 0

    def increment_action_index(self):
        self.action_index += 1

    def set_action_index(self, index):
        self.action_index = index

    def get_action_index(self):
        return self.action_index

    def add_loop_start(self, loop_number, index):
        self.loop_starts[loop_number] = index

    def get_loop_start(self, loop_number):
        return self.loop_starts.get(loop_number)

    def push_loop_stack(self, loop_number):
        self.loop_stack.append(loop_number)

    def pop_loop_stack(self):
        return self.loop_stack.pop() if self.loop_stack else None

    def peek_loop_stack(self):
        return self.loop_stack[-1] if self.loop_stack else None
