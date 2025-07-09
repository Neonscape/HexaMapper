import sys
from typing import override
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QObject, QEvent, Qt

class MapPanelEventHandler(QObject):
    
    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            print("Key Pressed")
            return True
        return super().eventFilter(obj, event)