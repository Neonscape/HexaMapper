from pydantic import BaseModel
from utils.color import RGBAColor as Color
from modules.config import app_config
from modules.tools.base_tool import ToolBase
from PyQt6.QtCore import QEvent
from modules.history_manager import PaintCellCommand
from modules.map_helpers import global_pos_to_global_coord
import numpy as np
from typing import override

class DrawToolSettings(BaseModel):
    radius: float = 1.0
    color: Color = Color([1.0, 1.0, 1.0, 1.0])

class DrawTool(ToolBase):
    def __init__(self, map_engine):
        super().__init__(map_engine)
        self.settings = DrawToolSettings()
        
    @override
    def mouse_press(self, event: QEvent):
        ...

    @override
    def mouse_move(self, event: QEvent):
        world_pos = self.map_engine._screen_to_world((event.pos().x(), event.pos().y()))
        world_coord = global_pos_to_global_coord(world_pos)
        
        color = np.array(self.settings.color.to_floats(), dtype=np.float32)

        command = PaintCellCommand(
            chunk_engine=self.map_engine.chunk_manager,
            global_coords=world_coord,
            new_color=color
        )
        self.map_engine.history_manager.execute(command)
        self.map_engine.map_panel.update()
    
    @override
    def mouse_release(self, event: QEvent):
        self.map_engine.history_manager.finish_action()
    
