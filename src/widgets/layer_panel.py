from loguru import logger
from modules.chunk_engine import ChunkEngine
from modules.icon_manager import IconManager
from modules.map_engine import MapEngine2D
from widgets.layer_entry import LayerEntry, LayerListItem
from qtpy.QtWidgets import (
    QListWidget,
    QAbstractItemView,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QListWidgetItem
)


class LayerEntryContainer(QListWidget):
    def __init__(
        self,
        icon_manager: IconManager,
        chunk_engine: ChunkEngine,
        map_engine: MapEngine2D,
        parent=None
    ):
        super().__init__(parent=parent)
        self.icon_manager = icon_manager
        self.chunk_engine = chunk_engine
        self.map_engine = map_engine
        self.entries = []
        self.items = []
        self.build_entries()
        
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        
        self.itemClicked.connect(self._handle_item_clicked)
        
        self.model().rowsMoved.connect(self._handle_rows_moved)
    
    def build_entries(self):
        self.clear()
        self.entries = [LayerEntry(self.icon_manager, self.chunk_engine, self.map_engine, layer) for layer in self.chunk_engine.layers]
        self.items = [LayerListItem(entry) for entry in self.entries[::-1]]
        for item in self.items:
            self.addItem(item)
            self.setItemWidget(item, item.layer_entry)
        self.setCurrentItem(self.items[len(self.items) - self.chunk_engine.current_layer - 1])
        
    def _handle_rows_moved(self, parent, start, end, destination, row_count):
        """
        This slot is called when a row is moved successfully by the drag-and-drop operation.
        The `parent` and `row_count` arguments can be ignored for this simple case.
        
        - `start`: The index of the item that was dragged.
        - `end`: The index of the item that was dragged (for a single item, this is the same as `start`).
        - `destination`: The destination index where the item was dropped.
        """
        
        total = len(self.entries)
        from_idx = total - start - 1
        to_idx = total - row_count
        
        print(from_idx, to_idx, len(self.entries))

        # The QListWidget reorders its items *before* this signal is emitted.
        # The destination index is where the item *would have been* if the
        # list wasn't reordered yet.
        # To get the correct new index after the move, we need to adjust `to_idx`.
        # If the item was dragged downwards, the new index is `destination - 1`.
        # If it was dragged upwards, the new index is `destination`.
        if to_idx > from_idx:
            to_idx -= 1
        
        if from_idx != to_idx:
            self.chunk_engine.reorder_layer(from_idx, to_idx)
            
            # The UI is already reordered, so we just need to re-sync our entries list
            self.build_entries()
            
    def _handle_item_clicked(self, item: QListWidgetItem):
        idx = len(self.items) - self.items.index(item) - 1
        self.chunk_engine.current_layer = idx
        logger.debug(f"Set active layer to {idx}")
            
        
class LayerPanel(QWidget):
    def __init__(
        self,
        icon_manager: IconManager,
        chunk_engine: ChunkEngine,
        map_engine: MapEngine2D,
        parent=None
    ):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.chunk_engine = chunk_engine
        self.map_engine = map_engine
        
        self.layer_entry_container = LayerEntryContainer(icon_manager, chunk_engine, map_engine, parent=self)

        self.layout = QVBoxLayout()
        self.btns_layout = QHBoxLayout()
        
        self.add_btn = QPushButton(icon_manager.get_icon("plus"), "", self)
        # TODO: refactor this to process LayerEntryContainer
        self.add_btn.clicked.connect(self._add_layer_callback)
        
        self.minus_btn = QPushButton(icon_manager.get_icon("minus"), "", self)
        self.minus_btn.clicked.connect(self._delete_layer_callback)
        
        self.up_btn = QPushButton(icon_manager.get_icon("up"), "", self)
        self.up_btn.clicked.connect(self._move_layer_up_callback)
        
        self.down_btn = QPushButton(icon_manager.get_icon("down"), "", self)
        self.down_btn.clicked.connect(self._move_layer_down_callback)

        self.btns_layout.addWidget(self.add_btn)
        self.btns_layout.addWidget(self.minus_btn)
        self.btns_layout.addWidget(self.up_btn)
        self.btns_layout.addWidget(self.down_btn)
        
        self.text_label = QLabel("Layers", self)
        
        self.layout.addWidget(self.text_label)
        self.layout.addLayout(self.btns_layout)
        self.layout.addWidget(self.layer_entry_container)

        self.setLayout(self.layout)
        
    def _add_layer_callback(self):
        self.chunk_engine.insert_layer()
        self.layer_entry_container.build_entries()
        
    def _delete_layer_callback(self):
        self.chunk_engine.delete_active_layer()
        self.layer_entry_container.build_entries()
        
    def _move_layer_up_callback(self):
        self.chunk_engine.reorder_layer(self.chunk_engine.current_layer, self.chunk_engine.current_layer + 1)
        self.layer_entry_container.build_entries()
        
    def _move_layer_down_callback(self):
        self.chunk_engine.reorder_layer(self.chunk_engine.current_layer, self.chunk_engine.current_layer - 1)
        self.layer_entry_container.build_entries()
        
        
        