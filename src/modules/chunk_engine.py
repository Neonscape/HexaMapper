from modules.config import ApplicationConfig
from modules.map_helpers import global_coord_to_chunk_coord
from loguru import logger
import numpy as np
from qtpy.QtCore import QObject, Signal

class ChunkLayer:
    """
    Manages the hex map data by organizing it into chunks.
    Handles creation, retrieval, and modification of cell data within these chunks,
    and tracks which chunks have been modified ("dirty chunks").
    """
    def __init__(self, config: ApplicationConfig, desc: str = "Layer 0"):
        """
        Initializes the ChunkEngine.
        """
        self.desc: str = desc
        self.is_visible: bool = True
        self.config = config
        self.chunks: dict[tuple[int, int], np.ndarray] = {}             # data of all chunks
        self.modified_cells : set[tuple[int, int]] = set()   # only user-modified chunks in here
        self.dirty_chunks : set[tuple[int, int]] = set()                # temporary buffer of modified chunks
        
    def reset(self):
        """
        Resets the chunk engine to its initial state.
        """
        for cell in self.modified_cells.copy():
            self.delete_cell_data(cell)
        self.chunks.clear()
        self.dirty_chunks.clear()
        self.modified_cells.clear()
        

    def _get_or_create_chunk(self, chunk_coord: tuple[int, int]) -> np.ndarray:
        """
        Retrieves a chunk's data. If the chunk does not exist, it is created and initialized
        with default cell colors.

        :param chunk_coord: The (x, y) coordinate of the chunk.
        :type chunk_coord: tuple[int, int]
        :return: The NumPy array containing the chunk data.
        :rtype: np.ndarray
        """
        if chunk_coord not in self.chunks:
            chunk_size = self.config.hex_map_engine.chunk_size
            data_dims = self.config.hex_map_engine.data_dimensions
            default_color = self.config.hex_map_custom.default_cell_color
            self.chunks[chunk_coord] = np.full((chunk_size, chunk_size, data_dims), default_color, dtype=np.float32)
            return self.chunks[chunk_coord]
        return self.chunks[chunk_coord]
    
    
    def set_cell_data(self, global_coords: tuple[int, int], data: np.ndarray) -> None:
        """
        Sets the data (e.g., color) for a specific cell at global coordinates.
        Marks the containing chunk as dirty.

        :param global_coords: The global (x, y) coordinates of the cell.
        :type global_coords: tuple[int, int]
        :param data: The data (e.g., RGBA color array) to write to the cell.
        :type data: np.ndarray
        """
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(global_coords, self.config.hex_map_engine.chunk_size)
        chunk_data = self._get_or_create_chunk((chunk_x, chunk_y))
        chunk_data[local_x, local_y] = data
        self.dirty_chunks.add((chunk_x, chunk_y))
        self.modified_cells.add(global_coords)
        
    def delete_cell_data(self, global_coords: tuple[int, int]) -> None:
        """
        Deletes the data (e.g., color) for a specific cell at global coordinates.
        Marks the containing chunk as dirty.
        
        :param global_coords: The global (x, y) coordinates of the cell.
        :type global_coords: tuple[int, int]
        """
        if global_coords not in self.modified_cells:
            return
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(global_coords, self.config.hex_map_engine.chunk_size)
        chunk_data = self._get_or_create_chunk((chunk_x, chunk_y))
        chunk_data[local_x, local_y] = self.config.hex_map_custom.default_cell_color
        self.dirty_chunks.add((chunk_x, chunk_y))
        self.modified_cells.remove(global_coords)
        

    def get_cell_data(self, global_coords: tuple[int, int]) -> np.ndarray:
        """
        Retrieves the data (e.g., color) for a specific cell at global coordinates.

        :param global_coords: The global (x, y) coordinates of the cell.
        :type global_coords: tuple[int, int]
        :return: The NumPy array containing the cell data.
        :rtype: np.ndarray
        """
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(global_coords, self.config.hex_map_engine.chunk_size)
        chunk_data = self._get_or_create_chunk((chunk_x, chunk_y))
        return chunk_data[local_x, local_y]
        
    def get_chunk_data(self, chunk_coord: tuple[int, int]) -> np.ndarray:
        """
        Retrieves the entire data array for a given chunk.

        :param chunk_coord: The (x, y) coordinate of the chunk.
        :type chunk_coord: tuple[int, int]
        :return: The NumPy array containing the chunk's data.
        :rtype: np.ndarray
        """
        
        return self._get_or_create_chunk(chunk_coord=chunk_coord)
    
    def get_and_clear_dirty_chunks(self) -> list[tuple[int, int]]:
        """
        Retrieves the list of dirty chunks (chunks that have been modified)
        and then clears the internal dirty list.

        :return: A list of (chunk_x, chunk_y) coordinates for dirty chunks.
        :rtype: list[tuple[int, int]]
        """
        
        dirty = list(self.dirty_chunks)
        self.dirty_chunks.clear()
        return dirty


class ChunkEngine(QObject):
    need_repaint = Signal()
    rebuild_entries = Signal()
    
    def __init__(self, config: ApplicationConfig):
        super().__init__()
        self.config = config
        self.layers: list[ChunkLayer] = [ChunkLayer(config)]
        self.active_layer_idx: int = 0
        self.name_cnt: int = 1
        self.dirty_chunks : set[tuple[int, int]] = set()
        
    def reset(self):
        """
        Resets the chunk engine to its initial state.
        """
        for l in self.layers:
            for cell in l.modified_cells:
                chunk_x, chunk_y, _, _ = global_coord_to_chunk_coord(cell, self.config.hex_map_engine.chunk_size)
                self.dirty_chunks.add((chunk_x, chunk_y))
        self.layers.clear()
        self.name_cnt = 1
        self.layers.append(ChunkLayer(self.config))
        self.active_layer_idx = 0
    
    def set_cell_data(self, global_coord: tuple[int, int], data: np.ndarray, layer: ChunkLayer = None):

        if layer is None:
            layer = self.layers[self.active_layer_idx]
        layer.set_cell_data(global_coords=global_coord, data=data)
        
    def delete_cell_data(self, global_coord: tuple[int, int], layer: ChunkLayer = None):
        if layer is None:
            layer = self.layers[self.active_layer_idx]
        layer.delete_cell_data(global_coords=global_coord)
        
    def get_cell_data(self, global_coord: tuple[int, int], layer: ChunkLayer = None) -> np.ndarray:
        if layer is None:
            layer = self.layers[self.active_layer_idx]
        return layer.get_cell_data(global_coords=global_coord)
    
    def get_layer_cell_data(self, layer: int, global_coord: tuple[int, int]) -> np.ndarray:
        return self.layers[layer].get_cell_data(global_coords=global_coord)
    
    def get_chunk_data(self, chunk_coord: tuple[int, int], layer: ChunkLayer = None) -> np.ndarray:
        """returns the data of the chunk at the given coordinates;
        if the layer param is not provided, defaults to visible data

        Args:
            chunk_coord (tuple[int, int]): chunk pos for data
            layer (ChunkLayer, optional): the layer to obtain data from. Defaults to None.

        Returns:
            np.ndarray: chunk data.
        """
        if layer is not None:
            return layer.get_chunk_data(chunk_coord=chunk_coord)

        chunks = [l.get_chunk_data(chunk_coord) for l in self.layers if l.is_visible]
        modified_cells_list = [v for k, v in self.get_all_modified_cells().items() if self.layers[k].is_visible]
            
        final_chunk = np.tile(
                np.array(
                    self.config.hex_map_custom.default_cell_color.to_floats()
                    ).reshape((1, 1, 4)),
                (16, 16, 1)
            )
        
        if len(chunks) == 0:
            return final_chunk
        
        for i, chunk in enumerate(chunks):
            for cell in modified_cells_list[i]:
                chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(cell, self.config.hex_map_engine.chunk_size)
                if chunk_x != chunk_coord[0] or chunk_y != chunk_coord[1]:
                    continue;
                final_chunk[local_x, local_y] = chunk[local_x, local_y]
        
        # logger.debug(f"Chunks: {chunks}, Final merge result: {final_chunk}")
        
        return final_chunk
    
    def get_modified_cells_in_active_layer(self):
        return self.layers[self.active_layer_idx].modified_cells
    
    def get_all_modified_cells(self):
        return dict([(idx, self.layers[idx].modified_cells) for idx in range(len(self.layers))])
    
    def get_and_clear_dirty_chunks(self):
        if len(self.layers) == 0:
            return []
        dirty = list(self.layers[self.active_layer_idx].dirty_chunks)
        self.layers[self.active_layer_idx].dirty_chunks.clear()
        dirty_extra = list(self.dirty_chunks)
        self.dirty_chunks.clear()
        
        final = set(dirty + dirty_extra)
        return list(final)

    def insert_layer(self, desc:str = None, idx: int = None):
        if desc is None:
            desc = f"Layer {self.name_cnt}"
            self.name_cnt += 1
        if idx is None:
            idx = self.active_layer_idx + 1
        self.layers.insert(idx, ChunkLayer(self.config, desc))
        self.active_layer_idx = idx
        
    def get_active_layer(self):
        return self.layers[self.active_layer_idx]
    
    def get_active_layer_index(self):
        return self.active_layer_idx

    def toggle_visibility(self, layer: ChunkLayer):        
        layer.is_visible = not layer.is_visible
        
        
        # toggle the visibility mark and set the chunks
        # where cells have been modified as dirty.
        
        for cell in layer.modified_cells:
            chunk_x, chunk_y, _, _ = global_coord_to_chunk_coord(cell, self.config.hex_map_engine.chunk_size)
            self.dirty_chunks.add((chunk_x, chunk_y))
            
        self.need_repaint.emit()

