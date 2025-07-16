from copy import copy
from typing import List
from modules.commands.base_command import Command

class HistoryManager:
    """
    Manages the undo and redo history of commands in the application.
    Commands are grouped into "actions" which can be undone or redone as a single unit.
    """
    def __init__(self):
        """
        Initializes the HistoryManager with empty undo and redo stacks and a command buffer.
        """
        self.undo_stack: List[List[Command]] = []
        self.redo_stack: List[List[Command]] = []
        self.command_buffer: List[Command] = []

    def clear(self):
        """
        Clears the undo and redo stacks.
        """
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.command_buffer.clear()

    def execute(self, command: Command):
        """
        Executes a given command and adds it to the current command buffer.
        Clears the redo stack upon execution of a new command.

        :param command: The command to execute.
        :type command: Command
        """
        command.execute()
        self.command_buffer.append(command)
        self.redo_stack.clear()
        
    def finish_action(self):
        """
        Finalizes the current action by moving all commands from the command buffer
        to the undo stack. This makes the buffered commands a single undoable unit.
        """
        if self.command_buffer:
            self.undo_stack.append(copy(self.command_buffer))
            self.command_buffer.clear()

    def undo(self):
        """
        Undoes the last completed action by executing the undo method for each command
        in the last command block on the undo stack. Moves the undone action to the redo stack.
        """
        if not self.undo_stack:
            return
        command_block = self.undo_stack.pop()
        for command in reversed(command_block):
            command.undo()
        self.redo_stack.append(command_block)

    def redo(self):
        """
        Redoes the last undone action by executing the execute method for each command
        in the last command block on the redo stack. Moves the redone action back to the undo stack.
        """
        if not self.redo_stack:
            return
        command_block = self.redo_stack.pop()
        for command in command_block:
            command.execute()
        self.undo_stack.append(command_block)
