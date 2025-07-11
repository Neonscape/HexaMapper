from modules.config import app_config
from modules.map_helpers import *
from loguru import logger
import numpy as np

CHUNK_SIZE = app_config.hex_map_engine.chunk_size
DATA_DIMENSIONS = app_config.hex_map_engine.data_dimensions
DEFAULT_CELL_COLOR = app_config.hex_map_custom.default_cell_color

class ChunkEngine:
    """
    Manages the hex map data by organizing it into chunks.
    Handles creation, retrieval, and modification of cell data within these chunks,
    and tracks which chunks have been modified ("dirty chunks").
    """
    def __init__(self):
        """
        Initializes the ChunkEngine.
        """
        self.chunks: dict[tuple[int, int], np.ndarray] = {}
        self.dirty_chunks : set[tuple[int, int]] = set()
        
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
            self.chunks[chunk_coord] = np.full((CHUNK_SIZE, CHUNK_SIZE, DATA_DIMENSIONS), DEFAULT_CELL_COLOR, dtype=np.float32)
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
        logger.debug(f"Setting cell data at {global_coords} to {data}")
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(global_coords)
        chunk_data = self._get_or_create_chunk((chunk_x, chunk_y))
        chunk_data[local_x, local_y] = data
        self.dirty_chunks.add((chunk_x, chunk_y))

    def get_cell_data(self, global_coords: tuple[int, int]) -> np.ndarray:
        """
        Retrieves the data (e.g., color) for a specific cell at global coordinates.

        :param global_coords: The global (x, y) coordinates of the cell.
        :type global_coords: tuple[int, int]
        :return: The NumPy array containing the cell data.
        :rtype: np.ndarray
        """
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(global_coords)
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
