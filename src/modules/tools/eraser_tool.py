from typing import override
from modules.map_helpers import get_coords_within_radius, global_pos_to_global_coord
from modules.tools.base_tool import BaseToolConfig, ToolBase
from modules.commands.erase_cell_command import EraseCellCommand
from pydantic import Field
from qtpy.QtCore import QEvent

class EraserToolSettings(BaseToolConfig):
    radius: float = Field(
        default=1.0,
        title="半径",
        json_schema_extra={
            "ui_min": 1.0,
            "ui_max": 100.0
        }
    )
    


class EraserTool(ToolBase):
    """
    A tool for erasing cells on the hex map.
    """
    def __init__(self, map_engine):
        super().__init__(map_engine)
        self.settings = EraserToolSettings()

    @override
    def mouse_press(self, event: QEvent):
        pass

    @override
    def mouse_move(self, event: QEvent):
        world_pos = self.map_engine.screen_to_world((event.pos().x(), event.pos().y()))
        world_coord = global_pos_to_global_coord(world_pos, self.map_engine.config.hex_map_engine.hex_radius)
        
        covered_coords = get_coords_within_radius(world_pos, self.settings.radius, self.map_engine.config.hex_map_engine.hex_radius)
        
        command = EraseCellCommand(
            self.map_engine.chunk_engine,
            global_coords=covered_coords
        )
        
        self.map_engine.history_manager.execute(command)
        self.map_engine.map_panel.update()
        
    @override
    def mouse_release(self, event:QEvent):
        self.map_engine.history_manager.finish_action()
        
    
    @override
    def get_visual_aid_info(self):
        return {
            "shape": "circle",
            "radius": self.settings.radius,
            "color": (1.0, 0.0, 0.0, 0.5) # Red for erase
        }

    @override
    def get_settings(self):
        return self.settings