from pydantic import BaseModel
from utils.color import RGBAColor as Color
from modules.config import app_config
from modules.tools.base_tool import ToolBase
from PyQt6.QtCore import QEvent
from modules.commands.paint_cell_command import PaintCellCommand
from modules.map_helpers import global_pos_to_global_coord
import numpy as np
from typing import override

class DrawToolSettings(BaseModel):
    """
    Pydantic model for the settings of the DrawTool.
    """
    radius: float = 1.0
    color: Color = Color([1.0, 1.0, 1.0, 1.0])

class DrawTool(ToolBase):
    """
    A tool for drawing (painting) cells on the hex map.
    It uses the PaintCellCommand for undo/redo functionality.
    """
    def __init__(self, map_engine):
        """
        Initializes the DrawTool.

        :param map_engine: The MapEngine2D instance this tool will interact with.
        :type map_engine: MapEngine2D
        """
        super().__init__(map_engine)
        self.settings = DrawToolSettings()
        
    @override
    def mouse_press(self, event: QEvent):
        """
        Handles a mouse press event. Currently, this method does nothing.

        :param event: The mouse event.
        :type event: QEvent
        """
        pass

    @override
    def mouse_move(self, event: QEvent):
        """
        Handles a mouse move event. If a mouse button is pressed, it paints the cell
        under the cursor with the current tool color.

        :param event: The mouse event.
        :type event: QEvent
        """
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
        """
        Handles a mouse release event. Finishes the current drawing action,
        making it a single undoable unit.

        :param event: The mouse event.
        :type event: QEvent
        """
        self.map_engine.history_manager.finish_action()

    @override
    def get_visual_aid_info(self):
        """
        Returns information for rendering a circular visual aid for the draw tool.

        :return: A dictionary containing shape, radius, and color for the visual aid.
        :rtype: dict
        """
        return {
            "shape": "circle",
            "radius": self.settings.radius,
            "color": (1.0, 1.0, 1.0, 0.5)
        }
