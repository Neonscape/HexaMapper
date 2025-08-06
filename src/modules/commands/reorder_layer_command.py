from modules.commands.base_command import Command
from modules.chunk_engine import ChunkEngine
from modules.map_helpers import global_coord_to_chunk_coord

class ReorderLayerCommand(Command):
    def __init__(self, chunk_engine: ChunkEngine, from_index: int, to_index: int):
        self.layer = chunk_engine.layers.pop(from_index)
        self.chunk_engine = chunk_engine
        self.from_idx = from_index
        self.to_idx = to_index
        self.original_idx = chunk_engine.active_layer_idx

    def execute(self):
        self.chunk_engine.layers.insert(self.to_idx, self.layer)
        
        if self.chunk_engine.active_layer_idx == self.from_idx:
            self.chunk_engine.active_layer_idx = self.to_idx
        elif self.from_idx < self.active_layer_idx and self.to_idx > self.active_layer_idx:
            self.chunk_engine.active_layer_idx -= 1
        elif self.from_idx > self.active_layer_idx and self.to_idx < self.active_layer_idx:
            self.chunk_engine.active_layer_idx += 1
        
        # do a repaint
        for cell in self.layer.modified_cells:
            chunk_x, chunk_y, _, _ = global_coord_to_chunk_coord(cell, self.chunk_engine.config.hex_map_engine.chunk_size)
            self.chunk_engine.dirty_chunks.add((chunk_x, chunk_y))
        self.chunk_engine.need_repaint.emit()
        self.chunk_engine.rebuild_entries.emit()

    def undo(self):
        self.chunk_engine.layers.pop(self.to_idx)
        self.chunk_engine.layers.insert(self.from_idx, self.layer)

        # do a repaint
        for cell in self.layer.modified_cells:
            chunk_x, chunk_y, _, _ = global_coord_to_chunk_coord(cell, self.chunk_engine.config.hex_map_engine.chunk_size)
            self.chunk_engine.dirty_chunks.add((chunk_x, chunk_y))
            
        self.chunk_engine.active_layer_idx = self.original_idx
        
        self.chunk_engine.need_repaint.emit()
        self.chunk_engine.rebuild_entries.emit()