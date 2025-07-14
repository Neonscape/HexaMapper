from modules.chunk_engine import ChunkEngine
from modules.commands.base_command import Command

class EraseCellCommand(Command):
    def __init__(self, chunk_engine: ChunkEngine, global_coords: tuple[int, int]):
        self.chunk_engine = chunk_engine
        self.global_coords = global_coords
        self.previous_color = self.chunk_engine.get_cell_data(global_coords).copy()
        self.is_new = (global_coords not in self.chunk_engine.modified_cells)
        
    def execute(self):
        if not self.is_new:
            self.chunk_engine.delete_cell_data(self.global_coords)
            
    def undo(self):
        if not self.is_new:
            self.chunk_engine.set_cell_data(self.global_coords, self.previous_color)
        