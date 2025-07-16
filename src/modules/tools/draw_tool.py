from pydantic import Field
from utils.color import RGBAColor as Color
from modules.tools.base_tool import ToolBase
from qtpy.QtCore import QEvent
from modules.commands.paint_cell_command import PaintCellCommand
from modules.map_helpers import global_pos_to_global_coord
from modules.tools.base_tool import BaseToolConfig
from modules.map_helpers import get_coords_within_radius
import numpy as np
from typing import override

class DrawToolSettings(BaseToolConfig):
    """
    Pydantic model for the settings of the DrawTool.
    """
    radius: float = Field(
        default=1.0,
        title="半径",
        json_schema_extra={
            "ui_min": 1.0,
            "ui_max": 100.0
        }
    )
    color: Color = Field(default=Color([1.0, 1.0, 1.0, 1.0]), title="颜色")
    # TODO: refactor these to use localized strings

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
        world_pos = self.map_engine.screen_to_world((event.pos().x(), event.pos().y()))
        world_coord = global_pos_to_global_coord(world_pos, self.map_engine.config.hex_map_engine.hex_radius)
        
        color = np.array(self.settings.color.to_floats(), dtype=np.float32)
        
        covered_coords = get_coords_within_radius(world_pos, self.settings.radius, self.map_engine.config.hex_map_engine.hex_radius)

        command = PaintCellCommand(
            chunk_engine=self.map_engine.chunk_engine,
            global_coords=covered_coords,
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

    @override
    def get_settings(self):
        return self.settings