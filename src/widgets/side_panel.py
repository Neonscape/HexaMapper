from qtpy.QtWidgets import QWidget, QVBoxLayout

class SidePanel(QWidget):
    def __init__(self, widgets: list[QWidget], parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.widgets = widgets
        for widget in widgets:
            self.layout.addWidget(widget, 1)
            
        self.setLayout(self.layout)