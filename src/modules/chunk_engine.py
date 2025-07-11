from modules.config import app_config
from modules.map_helpers import *
from loguru import logger
import numpy as np

CHUNK_SIZE = app_config.hex_map_engine.chunk_size
DATA_DIMENSIONS = app_config.hex_map_engine.data_dimensions
DEFAULT_CELL_COLOR = app_config.hex_map_custom.default_cell_color

class ChunkEngine:
    def __init__(self):
        self.chunks: dict[tuple[int, int], np.ndarray] = {}
        self.dirty_chunks : set[tuple[int, int]] = set()
        
    def _get_or_create_chunk(self, chunk_coord: tuple[int, int]) -> np.ndarray:
        """Get a chunk's information (and creates it when non-exist).

        Args:
            chunk_coord (tuple[int, int]): the coordinate of the chunk

        Returns:
            _type_: the chunk data
        """
        if chunk_coord not in self.chunks:
            self.chunks[chunk_coord] = np.full((CHUNK_SIZE, CHUNK_SIZE, DATA_DIMENSIONS), DEFAULT_CELL_COLOR, dtype=np.float32)
        return self.chunks[chunk_coord]
    
    
    def set_cell_data(self, global_coords: tuple[int, int], data: np.ndarray) -> None:
        """Change a cell's data.

        Args:
            global_coords (tuple[int, int]): the global coords of the cell
            data (np.ndarray): the data to write
        """
        logger.debug(f"Setting cell data at {global_coords} to {data}")
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(global_coords)
        chunk_data = self._get_or_create_chunk((chunk_x, chunk_y))
        chunk_data[local_x, local_y] = data
        self.dirty_chunks.add((chunk_x, chunk_y))

    def get_cell_data(self, global_coords: tuple[int, int]) -> np.ndarray:
        """Get a cell's data."""
        chunk_x, chunk_y, local_x, local_y = global_coord_to_chunk_coord(global_coords)
        chunk_data = self._get_or_create_chunk((chunk_x, chunk_y))
        return chunk_data[local_x, local_y]
        
    def get_chunk_data(self, chunk_coord: tuple[int, int]) -> np.ndarray:
        """Get a chunk's data.

        Args:
            chunk_coord (tuple[int, int]): the chunk's coordinate

        Returns:
            np.ndarray: the chunk's data
        """
        
        return self._get_or_create_chunk(chunk_coord=chunk_coord)
    
    def get_and_clear_dirty_chunks(self) -> list[tuple[int, int]]:
        """Get the dirty chunks and clear the dirty list.

        Returns:
            list[tuple[int, int]]: the dirty chunks
        """
        
        dirty = list(self.dirty_chunks)
        self.dirty_chunks.clear()
        return dirty
