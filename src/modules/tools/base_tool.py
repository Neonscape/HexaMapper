from widgets.map_panel import MapPanel
from abc import abstractmethod, ABC
from PyQt6.QtCore import QEvent

class ToolBase(ABC):
    def __init__(self, canvas:MapPanel):
        self.canvas = canvas
        
    @abstractmethod
    def use(self, event:QEvent):
        """this method is called whenever the tool is called from events.
        Do the work in this function (e.g. draw to canvas for the draw tool)

        Args:
            event (QEvent): the event that triggered the tool
        """
        ...
    