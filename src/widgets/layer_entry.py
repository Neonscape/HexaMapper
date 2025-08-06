from qtpy.QtWidgets import QWidget, QPushButton, QSizePolicy, QLabel, QHBoxLayout
from modules.chunk_engine import ChunkEngine, ChunkLayer
from modules.icon_manager import IconManager
from modules.map_engine import MapEngine2D
from qtpy.QtWidgets import QListWidgetItem


class LayerEntry(QWidget):
    def __init__(
        self,
        icon_manager: IconManager,
        chunk_engine: ChunkEngine,
        map_engine: MapEngine2D,
        layer: ChunkLayer,
        parent=None
    ):
        super().__init__(parent)
        self.chunk_engine = chunk_engine
        self.map_engine = map_engine
        self.layer = layer
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Fix 2: Create a layout for LayerEntry
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Remove margins for a clean look

        self.label = QLabel(self.layer.desc, self)
        self.icon_visible = icon_manager.get_icon("visible")
        self.icon_hidden = icon_manager.get_icon("invisible")
        self.btn = QPushButton(
            self.icon_visible if self.layer.is_visible else self.icon_hidden,
            "",
            self
        )
        self.btn.clicked.connect(self.toggle_visibility)

        # Add the widgets to the new layout
        layout.addWidget(self.btn, 1)
        layout.addWidget(self.label, 5)
        
    def toggle_visibility(self):
        self.layer.is_visible = not self.layer.is_visible
        self.btn.setIcon(self.icon_visible if self.layer.is_visible else self.icon_hidden)
        self.map_engine.map_panel.update()

class LayerListItem(QListWidgetItem):
    def __init__(self, layer_entry: LayerEntry, parent=None):
        super().__init__(parent=parent)
        self.layer_entry = layer_entry
