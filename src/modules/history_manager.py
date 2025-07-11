from copy import copy
from typing import List
from modules.commands.base_command import Command

class HistoryManager:
    def __init__(self):
        # The history manager handles commands as blocks, where each block is called an "action"
        # e.g. a brush stroke "action" may paint multiple cells; 
        # while each cell is colored by a single command,
        # when undo is called the entire action is undone
        self.undo_stack: List[List[Command]] = []
        self.redo_stack: List[List[Command]] = []
        self.command_buffer: List[Command] = []

    def execute(self, command: Command):
        command.execute()
        self.command_buffer.append(command)
        self.redo_stack.clear()
        
    def finish_action(self):
        if self.command_buffer:
            self.undo_stack.append(copy(self.command_buffer))
            self.command_buffer.clear()

    def undo(self):
        if not self.undo_stack:
            return
        command_block = self.undo_stack.pop()
        for command in reversed(command_block):
            command.undo()
        self.redo_stack.append(command_block)

    def redo(self):
        if not self.redo_stack:
            return
        command_block = self.redo_stack.pop()
        for command in command_block:
            command.execute()
        self.undo_stack.append(command_block)
