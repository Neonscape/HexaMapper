from loguru import logger
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication
from pytablericons import TablerIcons, OutlineIcon

from utils.helpers import get_system_color_scheme

class IconManager:
    def __init__(self, app: QApplication):
        if get_system_color_scheme(app) == 'LIGHT':
            self.color = "#000000"
            logger.debug("System color scheme is LIGHT, using black color for icons")
        else:
            self.color = "#ffffff"
            logger.debug("System color scheme is DARK, using white color for icons")
        self.icons: dict[str, QIcon] = {}
        self._icon_map = {
            "undo": OutlineIcon.ARROW_BACK_UP,
            "redo": OutlineIcon.ARROW_FORWARD,
            "save": OutlineIcon.DEVICE_FLOPPY,
            "draw": OutlineIcon.BRUSH,
            "erase": OutlineIcon.ERASER,
            "pipe": OutlineIcon.TEST_PIPE,
            "visible": OutlineIcon.EYE,
            "invisible": OutlineIcon.EYE_CLOSED,
            "plus": OutlineIcon.PLUS,
            "minus": OutlineIcon.MINUS,
            "up": OutlineIcon.CARET_UP,
            "down": OutlineIcon.CARET_DOWN,
            "select": OutlineIcon.CLICK
            # add more icons here
        }
        self._init_icons()
        
    def _init_icons(self):
        for name, icon in self._icon_map.items():
            self.icons[name] = QIcon(TablerIcons.load(icon, color=self.color).toqpixmap())
            
    def get_icon(self, name: str) -> QIcon:
        return self.icons.get(name, QIcon()) # Return a default empty icon if not found
