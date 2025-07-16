"""
Helper functions for converting between different coordinate systems
(global coordinates, chunk coordinates, world positions, screen positions)
for the hexagonal map.
"""

from qtpy.QtCore import QPointF
from math import ceil, sqrt
from itertools import product

def get_coords_within_radius(pos: QPointF, radius: float, hex_radius: float):
    """
    Returns a list of global coordinates within a given radius from a specified position.

    :param pos: The position from which to calculate the coordinates.
    :type pos: QPointF
    :param radius: The radius within which to find the coordinates.
    :type radius: float
    :return: A list of tuples representing the global coordinates.
    :rtype: list[tuple[int, int]]
    """
    center_coord = global_pos_to_global_coord(pos, hex_radius)
    unit = ceil(radius / hex_radius)
    
    x_pos = [center_coord[0] + i for i in range(-unit, unit + 1)]
    y_pos = [center_coord[1] + j for j in range(-unit, unit + 1)]
    
    prob_coords = [(i, j) for i, j in product(x_pos, y_pos)]
    ret = []
    for coord in prob_coords:
        coord_pos = get_center_position_from_global_coord(coord, hex_radius)
        if (coord_pos[0] - pos.x()) ** 2 + (coord_pos[1] - pos.y()) ** 2 <= radius ** 2:
            ret.append(coord)
            
    return ret


def get_center_position_from_global_coord(global_coord: tuple[int, int], hex_radius: float) -> tuple[float, float]:
    """
    Calculates the world position (center) of a hexagon given its global coordinates.
    Uses an odd-q vertical layout for hexagonal grid.

    :param global_coord: A tuple (col, row) representing the global coordinates of the cell.
    :type global_coord: tuple[int, int]
    :param hex_radius: The radius of the hexagon.
    :type hex_radius: float
    :return: A tuple (x, y) representing the world position of the cell's center.
    :rtype: tuple[float, float]
    """
    col, row = global_coord
    # odd-q vertical layout
    x = hex_radius * 3 / 2 * col
    y = hex_radius * sqrt(3) * (row + 0.5 * col)
    return (x, y)


def global_coord_to_chunk_coord(global_coord: tuple[int, int], chunk_size: int) -> tuple[int, int, int, int]:
    """
    Determines which chunk a given global cell coordinate belongs to,
    and its local coordinates within that chunk.

    :param global_coord: The global (x, y) coordinates of the cell.
    :type global_coord: tuple[int, int]
    :param chunk_size: The size of the chunk.
    :type chunk_size: int
    :return: A tuple containing (chunk_x, chunk_y, local_x, local_y).
    :rtype: tuple[int, int, int, int]
    """
    return (global_coord[0] // chunk_size,
            global_coord[1] // chunk_size,
            global_coord[0] % chunk_size,
            global_coord[1] % chunk_size)


def global_pos_to_global_coord(global_pos: QPointF, hex_radius: float) -> tuple[int, int]:
    """
    Converts a world position (QPointF) to the nearest global hexagonal cell coordinate.

    :param global_pos: The world position.
    :type global_pos: QPointF
    :param hex_radius: The radius of the hexagon.
    :type hex_radius: float
    :return: A tuple (col, row) representing the global coordinates of the nearest cell.
    :rtype: tuple[int, int]
    """
    # Use proper horizontal scaling factor (1.5 * hex_radius)
    col_approx = global_pos.x() / (1.5 * hex_radius)
    
    # Use proper vertical scaling factor (sqrt(3) * hex_radius)
    row_approx = global_pos.y() / (sqrt(3) * hex_radius) - global_pos.x() / 3
    
    col = round(col_approx)
    row = round(row_approx)
    
    # Find the coordinates of the three closest hex centers
    candidates = []
    for r_offset in range(-1, 2):
        for c_offset in range(-1, 2):
            cand_row = row + r_offset
            cand_col = col + c_offset
            center_pos = get_center_position_from_global_coord((cand_col, cand_row), hex_radius)
            dist_sq = (global_pos.x() - center_pos[0])**2 + (global_pos.y() - center_pos[1])**2
            candidates.append(((cand_col, cand_row), dist_sq))
    
    # Find the one with the minimum distance
    best_coord, _ = min(candidates, key=lambda item: item[1])
    return best_coord
