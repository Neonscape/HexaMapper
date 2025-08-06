from typing import override
from modules.map_helpers import global_coord_to_chunk_coord, global_pos_to_global_coord
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
        
        # Test if the cells have been modified on at least one layer or not
        # if not, do not change the color
        
        modified_cells = self.map_engine.chunk_engine.get_all_modified_cells()
        is_modified = False
        
        for _, cells in modified_cells.items():
            if world_coord in cells:
                is_modified = True
                break
        
        if not is_modified:
            return
        
        # get the surface data of the chunk
        
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(world_coord, self.map_engine.config.hex_map_engine.chunk_size)
        chunk_coord = (chunk_x, chunk_y)
        
        chunk_data = self.map_engine.chunk_engine.get_chunk_data(chunk_coord)
        color = RGBAColor(chunk_data[local_x, local_y].flatten().tolist())
        draw_tool_settings = self.map_engine.tool_manager.get_tool("draw").settings
        draw_tool_settings.color = color
        logger.debug(f"Color set to {color}")
            
    
    @override
    def get_settings(self):
        return super().get_settings()
            
        