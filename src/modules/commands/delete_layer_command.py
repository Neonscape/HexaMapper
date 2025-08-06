from modules.commands.base_command import Command
from modules.chunk_engine import ChunkEngine, ChunkLayer
from modules.map_helpers import global_coord_to_chunk_coord

class DeleteLayerCommand(Command):
    def __init__(self, chunk_engine: ChunkEngine):
        
        self.removing_last_layer = False
        if len(chunk_engine.layers) == 1:
            self.removing_last_layer = True
        
        self.deleted_layer = chunk_engine.get_active_layer()
        self.inserted_layer = None
        self.chunk_engine = chunk_engine
        self.original_idx = chunk_engine.active_layer_idx

    def execute(self):
        # do a repaint in the affected chunks
        for cell in self.deleted_layer.modified_cells:
            chunk_x, chunk_y, _, _ = global_coord_to_chunk_coord(cell, self.chunk_engine.config.hex_map_engine.chunk_size)
            self.chunk_engine.dirty_chunks.add((chunk_x, chunk_y))
        self.chunk_engine.need_repaint.emit()
        
        self.chunk_engine.layers.remove(self.deleted_layer)
        
        self.chunk_engine.active_layer_idx = max(0, self.chunk_engine.active_layer_idx - 1)
        
        # if the layer removed is the last layer in stack,
        # then create a new layer and insert it into the stack
        if self.removing_last_layer:
            self.inserted_layer = ChunkLayer(self.chunk_engine.config, f"Layer {self.chunk_engine.name_cnt}")
            self.chunk_engine.name_cnt += 1
            self.chunk_engine.layers.append(self.inserted_layer)
        
        self.chunk_engine.rebuild_entries.emit()

    def undo(self):
        # remove the inserted layer
        if self.removing_last_layer:
            self.chunk_engine.layers.remove(self.inserted_layer)
            self.chunk_engine.name_cnt -= 1
            del self.inserted_layer
            # no repaint for new layer because it must be empty
            
        self.chunk_engine.layers.insert(self.original_idx, self.deleted_layer)
        self.chunk_engine.active_layer_idx = self.original_idx
        
        # do a repaint in the affected chunks
        for cell in self.deleted_layer.modified_cells:
            chunk_x, chunk_y, _, _ = global_coord_to_chunk_coord(cell, self.chunk_engine.config.hex_map_engine.chunk_size)
            self.chunk_engine.dirty_chunks.add((chunk_x, chunk_y))
        self.chunk_engine.need_repaint.emit()
        
        self.chunk_engine.rebuild_entries.emit()
            