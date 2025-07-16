from abc import ABC, abstractmethod
from qtpy.QtWidgets import QWidget

class BaseController(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
    
    @abstractmethod
    def update(self):
        pass