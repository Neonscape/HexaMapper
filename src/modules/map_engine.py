from widgets.map_panel import MapPanel
from modules.shader_manager import ShaderManager

class MapEngine2D:
    def __init__(self, map_panel: MapPanel):
        self.map_panel = map_panel
        self.shader_programs = ShaderManager()
        
    