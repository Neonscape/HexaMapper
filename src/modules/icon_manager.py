from PyQt6.QtGui import QIcon
from pytablericons import TablerIcons, OutlineIcon

class IconManager:
    def __init__(self):
        self.icons: dict[str, QIcon] = {}
        self.icon_map = {
            "undo": OutlineIcon.ARROW_BACK_UP,
            "redo": OutlineIcon.ARROW_BACK_DOWN,
            "save": OutlineIcon.DEVICE_FLOPPY,
            "draw": OutlineIcon.BRUSH,
            "erase": OutlineIcon.ERASER,
            # add more icons here
        }
        for name, icon in self.icon_map:
            self.icons[name] = QIcon(TablerIcons.load(icon))
        
    def get_icon(self, name: str) -> QIcon:
        return self.icons[name]

icon_manager = IconManager()
