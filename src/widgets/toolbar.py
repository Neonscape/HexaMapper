from typing import Callable
from PyQt6.QtWidgets import QToolBar, QPushButton
from modules.icon_manager import icon_manager as im


class CustomToolbar(QToolBar):
    """
    A custom toolbar widget for the application, managing tool buttons.
    """
    def __init__(self, name: str):
        """
        Initializes the CustomToolbar.

        :param name: The name of the toolbar.
        :type name: str
        """
        super().__init__(name)
        self.buttons : dict[str, QPushButton] = {}
        self.initUI()
    
    def register_tool_btn(self, tooltip: str, icon: str, callback: Callable, **args):
        """
        Registers a new tool button on the toolbar.

        :param tooltip: The tooltip text for the button.
        :type tooltip: str
        :param icon: The name of the icon to use for the button.
        :type icon: str
        :param callback: The function to call when the button is clicked.
        :type callback: Callable
        :param args: Additional keyword arguments.
        """
        btn = QPushButton(im.get_icon(icon), "", self) # Corrected QPushButton constructor arguments
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        self.addWidget(btn)
        self.buttons[tooltip] = btn
        
    def initUI(self):
        """
        Initializes the user interface components of the toolbar.
        """
        pass
