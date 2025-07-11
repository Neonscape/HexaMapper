from typing import Callable
from PyQt6.QtWidgets import QToolBar, QPushButton
from modules.icon_manager import icon_manager as im


class CustomToolbar(QToolBar):
    def __init__(self, name: str):
        super().__init__(name)
        self.buttons : dict[str, QPushButton] = {}
        self.initUI()
        # TODO: other initialization work?
    
    def register_tool_btn(self, tooltip: str, icon: str, callback: Callable, **args):
        btn = QPushButton(im.get_icon(icon), self)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        
    def initUI(self):
        pass