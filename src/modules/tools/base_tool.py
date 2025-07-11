from __future__ import annotations
from typing import TYPE_CHECKING
from abc import abstractmethod, ABC
from PyQt6.QtCore import QEvent

if TYPE_CHECKING:
    from modules.map_engine import MapEngine2D

class ToolBase(ABC):
    def __init__(self, map_engine:MapEngine2D):
        self.map_engine = map_engine
        
    def mouse_press(self, event:QEvent):
        ...

    def mouse_move(self, event:QEvent):
        ...

    def mouse_release(self, event:QEvent):
        ...

    def activate(self):
        ...

    def get_visual_aid_info(self):
        """
        Returns information for rendering a visual aid for the tool.
        If None, no visual aid is drawn.
        """
        return None

    def deactivate(self):
        ...
