from PyQt6.QtGui import QIcon
from pytablericons import TablerIcons, OutlineIcon

class IconManager:
    def __init__(self):
        self.icons: dict[str, QIcon] = {}
        self.icon_map = {
            "undo": OutlineIcon.ARROW_BACK_UP,
            "redo": OutlineIcon.ARROW_FORWARD,
            "save": OutlineIcon.DEVICE_FLOPPY,
            "draw": OutlineIcon.BRUSH,
            "erase": OutlineIcon.ERASER,
            # add more icons here
        }
        
        
    def init_icons(self):
        for name, icon in self.icon_map.items():
            self.icons[name] = QIcon(TablerIcons.load(icon).toqpixmap())
            
            
    def get_icon(self, name: str) -> QIcon:
        return self.icons[name]

icon_manager = IconManager()
