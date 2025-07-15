from __future__ import annotations
from typing import TYPE_CHECKING
from abc import abstractmethod, ABC
from qtpy.QtCore import QEvent
from pydantic import BaseModel

if TYPE_CHECKING:
    from modules.map_engine import MapEngine2D
    
class BaseToolConfig(BaseModel):
    """
    Base configuration model for tools.
    """
    ...

class ToolBase(ABC):
    """
    Abstract base class for all tools in the HexaMapper application.
    Defines the interface for tool interactions with the map engine.
    """
    def __init__(self, map_engine:MapEngine2D):
        """
        Initializes the base tool with a reference to the map engine.

        :param map_engine: The MapEngine2D instance this tool will interact with.
        :type map_engine: MapEngine2D
        """
        self.map_engine = map_engine
        
    def mouse_press(self, event:QEvent):
        """
        Handles a mouse press event.

        :param event: The mouse event.
        :type event: QEvent
        """
        ...

    def mouse_move(self, event:QEvent):
        """
        Handles a mouse move event.

        :param event: The mouse event.
        :type event: QEvent
        """
        ...

    def mouse_release(self, event:QEvent):
        """
        Handles a mouse release event.

        :param event: The mouse event.
        :type event: QEvent
        """
        ...

    def activate(self):
        """
        Called when the tool becomes active.
        """
        ...

    def get_visual_aid_info(self):
        """
        Returns information for rendering a visual aid for the tool.
        If None, no visual aid is drawn.

        :return: A dictionary containing visual aid information (e.g., shape, radius, color), or None.
        :rtype: dict | None
        """
        return None

    def deactivate(self):
        """
        Called when the tool becomes inactive.
        """
        ...
    
    @abstractmethod
    def get_settings(self):
        return None
