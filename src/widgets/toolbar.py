from typing import Callable
from PyQt6.QtWidgets import QToolBar, QPushButton
from modules.icon_manager import IconManager


class CustomToolbar(QToolBar):
    """
    A custom toolbar widget for the application, managing tool buttons.
    """
    def __init__(self, name: str, icon_manager: IconManager):
        """
        Initializes the CustomToolbar.

        :param name: The name of the toolbar.
        :type name: str
        :param icon_manager: The IconManager instance for retrieving icons.
        :type icon_manager: IconManager
        """
        super().__init__(name)
        self.icon_manager = icon_manager
        self.buttons : dict[str, QPushButton] = {}
    
    def register_tool_btn(self, name: str, tooltip: str, callback: Callable):
        """
        Registers a new tool button on the toolbar.

        :param name: The unique name of the tool (used for icon lookup and as a key).
        :type name: str
        :param tooltip: The tooltip text for the button.
        :type tooltip: str
        :param callback: The function to call when the button is clicked.
        :type callback: Callable
        """
        btn = QPushButton(self.icon_manager.get_icon(name), "", self)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        self.addWidget(btn)
        self.buttons[name] = btn
