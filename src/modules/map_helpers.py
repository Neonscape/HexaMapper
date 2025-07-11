# helper functions: cell-transform

from modules.config import app_config as conf
from PyQt6.QtCore import QPointF


def get_center_position_from_global_coord(global_coord: tuple[int, int]) -> tuple[float, float]:
    """Finds the world position of the given cell at the global coord.
    Args:
        global_coord (tuple[int, int]): _description_
    Returns:
        tuple[float, float]: _description_
    """
    from math import sqrt
    
    HEX_RADIUS = conf.hex_map_engine.hex_radius
    
    col, row = global_coord
    # odd-q vertical layout
    x = HEX_RADIUS * 3 / 2 * col
    y = HEX_RADIUS * sqrt(3) * (row + 0.5 * (col % 2))
    return (x, y)
    

def global_coord_to_chunk_coord(global_coord: tuple[int, int]) -> tuple[int, int, int, int]:
    """Finds which chunk the given cell is in and where is it in the chunk.
    Args:
        global_coord (tuple[int, int]): the global coord of the cell
    Returns:
        tuple[int, int, int, int]: [chunk_x, chunk_y, local_x, local_y]
    """
    CHUNK_SIZE = conf.hex_map_engine.chunk_size
    
    return (global_coord[0] // CHUNK_SIZE,
            global_coord[1] // CHUNK_SIZE,
            global_coord[0] % CHUNK_SIZE,
            global_coord[1] % CHUNK_SIZE)
    

def global_pos_to_global_coord(global_pos: QPointF) -> tuple[int, int]:
    """Finds the global coord of the cell at the given world position."""
    from math import sqrt
    
    HEX_RADIUS = conf.hex_map_engine.hex_radius
    
    # CORRECTED: Use proper horizontal scaling factor (1.5 * HEX_RADIUS)
    col_approx = global_pos.x() / (1.5 * HEX_RADIUS)
    
    # CORRECTED: Use proper vertical scaling factor (sqrt(3) * HEX_RADIUS)
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