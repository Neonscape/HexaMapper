from vcolorpicker import getColor
from qtpy.QtWidgets import QWidget, QPushButton, QLayout, QHBoxLayout, QLabel, QSizePolicy
from qtpy.QtGui import QPalette, QColor
from pydantic import BaseModel, Field
from utils.color import RGBAColor

class ColorController(QWidget):
    def __init__(self, label: str = "", model: BaseModel = None, model_field: str = "", parent = None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self._model = model
        self._field = model_field
        self.color: RGBAColor = getattr(model, model_field)
        self.label = QLabel(self, text=label)
        self.btn = QPushButton(self)
        self.layout: QLayout = QHBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn)
        self.btn.clicked.connect(self.on_btn_clicked)
        self.set_btn_color(self.color)
        
        
    
    def set_btn_color(self, color: RGBAColor):
        stylesheet = f"""
        QPushButton{{
            background-color: {color.to_hex(include_alpha=False)};
            color: #00000000;
        }}
        """
        self.setStyleSheet(stylesheet)
    
    def on_btn_clicked(self):
        self.color = RGBAColor(getColor(self.color.to_bytes()[:3]))
        self.set_btn_color(self.color)
        setattr(self._model, self._field, self.color)
        
        
        
        