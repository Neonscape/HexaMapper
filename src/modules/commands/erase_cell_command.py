from modules.chunk_engine import ChunkEngine
from modules.commands.base_command import Command

class EraseCellCommand(Command):
    def __init__(self, chunk_engine: ChunkEngine, global_coords: list[tuple[int, int]]):
        self.chunk_engine = chunk_engine
        self.global_coords = global_coords
        self.previous_color = {coord: self.chunk_engine.get_cell_data(coord).copy() for coord in global_coords}
        self.is_new = {coord: (coord not in self.chunk_engine.modified_cells) for coord in global_coords}
        
    def execute(self):
        for coord in self.global_coords:
            if not self.is_new[coord]:
                self.chunk_engine.delete_cell_data(coord)
            
    def undo(self):
        for coord in self.global_coords:
            if not self.is_new[coord]:
                self.chunk_engine.set_cell_data(coord, self.previous_color[coord])
        