"""
Helper functions for converting between different coordinate systems
(global coordinates, chunk coordinates, world positions, screen positions)
for the hexagonal map.
"""

from modules.config import app_config as conf
from PyQt6.QtCore import QPointF
from math import sqrt


def get_center_position_from_global_coord(global_coord: tuple[int, int]) -> tuple[float, float]:
    """
    Calculates the world position (center) of a hexagon given its global coordinates.
    Uses an odd-q vertical layout for hexagonal grid.

    :param global_coord: A tuple (col, row) representing the global coordinates of the cell.
    :type global_coord: tuple[int, int]
    :return: A tuple (x, y) representing the world position of the cell's center.
    :rtype: tuple[float, float]
    """
    
    HEX_RADIUS = conf.hex_map_engine.hex_radius
    
    col, row = global_coord
    # odd-q vertical layout
    x = HEX_RADIUS * 3 / 2 * col
    y = HEX_RADIUS * sqrt(3) * (row + 0.5 * (col % 2))
    return (x, y)
    

def global_coord_to_chunk_coord(global_coord: tuple[int, int]) -> tuple[int, int, int, int]:
    """
    Determines which chunk a given global cell coordinate belongs to,
    and its local coordinates within that chunk.

    :param global_coord: The global (x, y) coordinates of the cell.
    :type global_coord: tuple[int, int]
    :return: A tuple containing (chunk_x, chunk_y, local_x, local_y).
    :rtype: tuple[int, int, int, int]
    """
    CHUNK_SIZE = conf.hex_map_engine.chunk_size
    
    return (global_coord[0] // CHUNK_SIZE,
            global_coord[1] // CHUNK_SIZE,
            global_coord[0] % CHUNK_SIZE,
            global_coord[1] % CHUNK_SIZE)
    

def global_pos_to_global_coord(global_pos: QPointF) -> tuple[int, int]:
    """
    Converts a world position (QPointF) to the nearest global hexagonal cell coordinate.

    :param global_pos: The world position.
    :type global_pos: QPointF
    :return: A tuple (col, row) representing the global coordinates of the nearest cell.
    :rtype: tuple[int, int]
    """
    
    HEX_RADIUS = conf.hex_map_engine.hex_radius
    
    # Use proper horizontal scaling factor (1.5 * HEX_RADIUS)
    col_approx = global_pos.x() / (1.5 * HEX_RADIUS)
    
    # Use proper vertical scaling factor (sqrt(3) * HEX_RADIUS)
    row_approx = global_pos.y() / (sqrt(3) * HEX_RADIUS)
    
    col = round(col_approx)
    row = round(row_approx)
    
    # Find the coordinates of the three closest hex centers
    candidates = []
    for r_offset in range(-1, 2):
        for c_offset in range(-1, 2):
            cand_row = row + r_offset
            cand_col = col + c_offset
            center_pos = get_center_position_from_global_coord((cand_col, cand_row))
            dist_sq = (global_pos.x() - center_pos[0])**2 + (global_pos.y() - center_pos[1])**2
            candidates.append(((cand_col, cand_row), dist_sq))
    
    # Find the one with the minimum distance
    best_coord, _ = min(candidates, key=lambda item: item[1])
    return best_coord
