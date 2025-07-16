from typing import Callable, Dict
from qtpy.QtWidgets import QToolBar, QPushButton, QButtonGroup, QWidget, QHBoxLayout, QSizePolicy
from qtpy.QtCore import Qt # Import Qt for alignment flags
from modules.icon_manager import IconManager
from modules.tools.base_tool import ToolBase
from widgets.tool_config import ToolConfigWidget


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
        # self.setFixedHeight(60)
        self.layout().setSpacing(5)
        
        # QToolBar inherently manages its own layout.
        # If you want to put other widgets (like tool_configs) *alongside* the buttons
        # and manage their layout, you should create a central widget or separate toolbars/widgets.
        # For simplicity, we'll make a container widget for tool configs and add it to the toolbar.

        # Create a QButtonGroup for managing the tool buttons
        self.button_group = QButtonGroup(self) # Parent is self (the toolbar)
        self.button_group.setExclusive(True) # Ensure only one tool button can be active at a time
        self.button_group.buttonClicked.connect(self._handle_button_click)
        
        self.buttons: Dict[str, QPushButton] = {}
        self._button_callbacks: Dict[QPushButton, Callable] = {} # Store callbacks associated with each button
        
        self.addSeparator()
        
        # A container widget to hold all tool configuration widgets
        # This allows us to use a layout for the config widgets within the toolbar
        self.tool_config_container = QWidget(self)
        self.tool_config_layout = QHBoxLayout(self.tool_config_container)
        self.tool_config_layout.setContentsMargins(0, 0, 0, 0) # Remove margins for compact layout
        self.tool_config_layout.setSpacing(5) # Add some spacing between config widgets
        
        # Stores tool config widgets, keyed by their associated QPushButton
        self.tool_configs: Dict[QPushButton, ToolConfigWidget] = {} 
        self._current_active_tool_config: ToolConfigWidget = None # To keep track of the currently visible config
        

    def _handle_button_click(self, button: QPushButton):
        """
        Internal handler for all button clicks managed by the QButtonGroup.
        Dispatches to the specific callback registered for the clicked button.
        """
        # Hide the previously active tool config widget
        if self._current_active_tool_config:
            self._current_active_tool_config.setVisible(False)

        # Show the tool config widget associated with the clicked button
        if button in self.tool_configs:
            clicked_tool_config = self.tool_configs[button]
            clicked_tool_config.setVisible(True)
            self._current_active_tool_config = clicked_tool_config # Update the active config
            clicked_tool_config.update()

        # Call the original callback associated with the button
        callback = self._button_callbacks.get(button)
        if callback:
            callback()

    def register_tool(self, tool: ToolBase, name: str, tooltip: str, callback: Callable):
        """
        Registers a new tool on the toolbar.

        :param tool: The tool instance to register.
        :type tool: ToolBase
        :param name: The unique name of the tool (used for icon lookup and as a key).
        :type name: str
        :param tooltip: The tooltip text for the button.
        :type tooltip: str
        :param callback: The function to call when the button is clicked.
        :type callback: Callable
        """
        btn = QPushButton(self.icon_manager.get_icon(name), "", self)
        btn.setCheckable(True) # Make buttons checkable for exclusive behavior
        btn.setToolTip(tooltip)
        
        self.addWidget(btn) # Add button directly to the toolbar
        self.button_group.addButton(btn) # Add the button to the QButtonGroup
        
        self.buttons[name] = btn # Keep a mapping by name if needed elsewhere
        self._button_callbacks[btn] = callback # Store the callback for later dispatch
        
        if not tool.get_settings():
            return
        
        tool_widget = ToolConfigWidget(tool, parent=self.tool_config_container) # Parent the config widget to its container
        self.tool_configs[btn] = tool_widget # Key by QPushButton instance
        
        # Add the tool_widget to the tool_config_layout, not directly to the toolbar
        self.tool_config_layout.addWidget(tool_widget)
        tool_widget.setVisible(False) # Initially hide all tool config widgets

        # If this is the first tool registered, make it active by default
        if not self._current_active_tool_config:
            btn.setChecked(True) # Visually check the button
            self._handle_button_click(btn) # Programmatically trigger its activation
            
    def finalize(self):
        self.addSeparator()
        self.addWidget(self.tool_config_container)