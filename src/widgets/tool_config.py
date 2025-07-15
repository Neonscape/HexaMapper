from modules.tools.base_tool import BaseToolConfig, ToolBase
from qtpy.QtWidgets import QWidget, QHBoxLayout, QLayout, QSizePolicy
from qtpy.QtCore import Qt
from widgets.controllers.color_controller import ColorController
from widgets.controllers.numeric_controller import NumericController

from utils.color import RGBAColor

class ToolConfigWidget(QWidget):
    def __init__(self, tool: ToolBase, parent = None, flags : Qt.WindowType = Qt.WindowType.Widget):
        super().__init__(parent, flags)
        
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        
        # automatically construct widgets based on config items
        data = tool.get_settings()
        if data is None:
            return
        cls = tool.get_settings().__class__
        
        self.controllers: dict[str, QWidget] = {}
        self.layout: QLayout = QHBoxLayout(self)
        self.layout.setDirection(QHBoxLayout.Direction.LeftToRight)
        self.layout.setSpacing(1)
        
        
        for field_name, field_info in cls.model_fields.items():
            field_type = field_info.annotation
            if field_type is None:
                continue
            
            if field_type == int or field_type == float:
                controller = NumericController(
                    field_info.title,
                    field_info.json_schema_extra['ui_min'],
                    field_info.json_schema_extra['ui_max'],
                    getattr(data, field_name),
                    step=1,
                    decimals=0 if field_type == int else 1,
                    parent=self,
                    model=data,
                    model_field=field_name
                )
                self.controllers[field_name] = controller
                self.layout.addWidget(controller)
            elif field_type == RGBAColor:
                controller = ColorController(
                    label=field_info.title,
                    model=data,
                    model_field=field_name,
                    parent=self
                )
                self.controllers[field_name] = controller
                self.layout.addWidget(controller)