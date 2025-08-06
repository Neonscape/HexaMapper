from modules.commands.base_command import Command
from modules.chunk_engine import ChunkEngine, ChunkLayer

class NewLayerCommand(Command):
    def __init__(self, chunk_engine: ChunkEngine):
        self.chunk_engine = chunk_engine
        self.layer : ChunkLayer = None
        self.original_idx = chunk_engine.active_layer_idx

    def execute(self):
        idx = self.chunk_engine.active_layer_idx + 1
        self.layer = ChunkLayer(self.chunk_engine.config, f"Layer {self.chunk_engine.name_cnt}")
        self.chunk_engine.name_cnt += 1
        self.chunk_engine.layers.insert(idx, self.layer)
        self.chunk_engine.active_layer_idx = idx
        self.chunk_engine.rebuild_entries.emit()
    
    def undo(self):
        self.chunk_engine.layers.remove(self.layer)
        self.chunk_engine.name_cnt -= 1
        self.chunk_engine.active_layer_idx = self.original_idx
        
        # we do not need to mark dirty chunks 
        # since the layer must be empty when undoing this command
        
        self.chunk_engine.rebuild_entries.emit()
        