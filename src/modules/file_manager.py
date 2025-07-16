from __future__ import annotations
from typing import TYPE_CHECKING
from modules.chunk_engine import ChunkEngine
import struct
from loguru import logger
from PIL import Image, ImageDraw
import numpy as np
from OpenGL.GL import *
from modules.map_helpers import get_center_position_from_global_coord, global_coord_to_chunk_coord

if TYPE_CHECKING:
    from modules.map_engine import MapEngine2D

class FileManager:
    """
    Manages file operations such as saving, loading, and exporting maps.
    """

    MAGIC_NUMBER = b"HMAP"
    VERSION = 1

    def __init__(self, chunk_engine: ChunkEngine, map_engine: MapEngine2D):
        """
        Initializes the FileManager.

        :param chunk_engine: The ChunkEngine instance for accessing map data.
        :type chunk_engine: ChunkEngine
        :param map_engine: The MapEngine2D instance for exporting the map.
        :type map_engine: MapEngine2D
        """
        self.chunk_engine = chunk_engine
        self.map_engine = map_engine

    def save_map(self, filepath: str):
        """
        Saves the current map data to a binary file.

        :param filepath: The path to the file where the map will be saved.
        :type filepath: str
        """
        try:
            with open(filepath, "wb") as f:
                # Write header
                f.write(self.MAGIC_NUMBER)
                f.write(struct.pack("I", self.VERSION))

                # Write modified cells
                for coord in self.chunk_engine.modified_cells:
                    color = self.chunk_engine.get_cell_data(coord)
                    # Each record: x (int), y (int), r, g, b, a (float32)
                    f.write(struct.pack("iiffff", coord[0], coord[1], *color))
            logger.info(f"Map saved to {filepath}")
        except IOError as e:
            logger.error(f"Error saving map to {filepath}: {e}")

    def load_map(self, filepath: str):
        """
        Loads map data from a binary file.

        :param filepath: The path to the file from which to load the map.
        :type filepath: str
        """
        try:
            with open(filepath, "rb") as f:
                # Read and verify header
                magic = f.read(4)
                if magic != self.MAGIC_NUMBER:
                    raise ValueError("Not a valid .hmap file.")
                version = struct.unpack("I", f.read(4))[0]
                if version != self.VERSION:
                    raise ValueError(f"Unsupported version: {version}")

                # Clear existing map data
                self.chunk_engine.reset()

                # Read modified cells
                while True:
                    chunk = f.read(24)
                    if not chunk:
                        break
                    x, y, r, g, b, a = struct.unpack("iiffff", chunk)
                    self.chunk_engine.set_cell_data((x, y), np.array([r, g, b, a], dtype=np.float32))
            
            # self.map_engine.update_and_render_chunks()
            logger.info(f"Map loaded from {filepath}")
        except (IOError, ValueError) as e:
            logger.error(f"Error loading map from {filepath}: {e}")

    def export_map_as_png(self, filepath: str):
        """
        Exports the entire map as a PNG image.

        :param filepath: The path to the file where the image will be saved.
        :type filepath: str
        """
        try:
            image_data = self.map_engine.map_panel.export_to_image()
            if image_data:
                pixels, width, height = image_data
                image = Image.frombytes("RGBA", (width, height), pixels)
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
                image.save(filepath, "PNG")
                logger.info(f"Map exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting map to {filepath}: {e}")
