from modules.commands.base_command import Command
from modules.chunk_engine import ChunkEngine
import numpy as np


class PaintCellCommand(Command):
    """
    A command to paint a specific cell on the hex map with a new color.
    Supports undo functionality to revert the cell to its previous color.
    """
    def __init__(self, chunk_engine: ChunkEngine, global_coords: tuple[int, int], new_color: np.ndarray):
        """
        Initializes the PaintCellCommand.

        :param chunk_engine: The ChunkEngine instance to modify.
        :type chunk_engine: ChunkEngine
        :param global_coords: The global (x, y) coordinates of the cell to paint.
        :type global_coords: tuple[int, int]
        :param new_color: The new RGBA color to apply to the cell.
        :type new_color: np.ndarray
        """
        self.chunk_engine = chunk_engine
        self.global_coords = global_coords
        self.new_color = new_color
        self.previous_color = self.chunk_engine.get_cell_data(global_coords).copy()

    def execute(self):
        """
        Executes the command, setting the cell's color to the new color.
        """
        self.chunk_engine.set_cell_data(self.global_coords, self.new_color)

    def undo(self):
        """
        Undoes the command, reverting the cell's color to its previous state.
        """
        self.chunk_engine.set_cell_data(self.global_coords, self.previous_color)
