from modules.commands.base_command import Command
from modules.chunk_engine import ChunkEngine, ChunkLayer
import numpy as np


class PaintCellCommand(Command):
    """
    A command to paint a specific cell on the hex map with a new color.
    Supports undo functionality to revert the cell to its previous color.
    """
    def __init__(self, chunk_engine: ChunkEngine, global_coords: list[tuple[int, int]], new_color: np.ndarray):
        """
        Initializes the PaintCellCommand.

        :param chunk_engine: The ChunkEngine instance to modify.
        :type chunk_engine: ChunkEngine
        :param global_coords: The global (x, y) coordinates of the cells to paint.
        :type global_coords: list[tuple[int, int]]
        :param new_color: The new RGBA color to apply to the cell.
        :type new_color: np.ndarray
        """
        self.chunk_engine = chunk_engine
        self.global_coords = global_coords
        self.new_color = new_color
        self.layer = chunk_engine.get_active_layer()
        self.previous_color = {coord: self.chunk_engine.get_cell_data(coord).copy() for coord in global_coords}
        self.is_new = {coord: (coord not in self.chunk_engine.get_modified_cells_in_active_layer()) for coord in global_coords}

    def execute(self):
        """
        Executes the command, setting the cell's color to the new color.
        """
        for coord in self.global_coords:
            self.chunk_engine.set_cell_data(coord, self.new_color)

    def undo(self):
        """
        Undoes the command, reverting the cell's color to its previous state.
        """
        for coord in self.global_coords:
            if self.is_new[coord]:
                self.chunk_engine.delete_cell_data(coord, layer=self.layer)
            else:
                self.chunk_engine.set_cell_data(coord, self.previous_color[coord], layer=self.layer)
