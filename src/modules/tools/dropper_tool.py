from typing import override
from modules.map_helpers import global_pos_to_global_coord
from modules.tools.base_tool import ToolBase
from qtpy.QtCore import QEvent
from loguru import logger

from utils.color import RGBAColor

class DropperTool(ToolBase):
    def __init__(self, map_engine):
        super().__init__(map_engine)
    
    @override
    def mouse_press(self, event:QEvent):
        world_pos = self.map_engine.screen_to_world((event.pos().x(), event.pos().y()))
        world_coord = global_pos_to_global_coord(world_pos, self.map_engine.config.hex_map_engine.hex_radius)
        
        if world_coord in self.map_engine.chunk_engine.modified_cells:
            color = RGBAColor(self.map_engine.chunk_engine.get_cell_data(world_coord).flatten().tolist())
            draw_tool_settings = self.map_engine.tool_manager.get_tool("draw").settings
            draw_tool_settings.color = color
            logger.debug(f"Color set to {color}")
    
    @override
    def get_settings(self):
        return super().get_settings()
            
        