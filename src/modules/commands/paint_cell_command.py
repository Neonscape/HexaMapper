from modules.commands.base_command import Command
from modules.chunk_engine import ChunkEngine
import numpy as np


class PaintCellCommand(Command):
    def __init__(self, chunk_engine: ChunkEngine, global_coords: tuple[int, int], new_color: np.ndarray):
        self.chunk_engine = chunk_engine
        self.global_coords = global_coords
        self.new_color = new_color
        self.previous_color = self.chunk_engine.get_cell_data(global_coords).copy()

    def execute(self):
        self.chunk_engine.set_cell_data(self.global_coords, self.new_color)

    def undo(self):
        # TODO: Refactor code to delete the cell data if it is previously empty
        self.chunk_engine.set_cell_data(self.global_coords, self.previous_color)