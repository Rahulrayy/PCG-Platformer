import numpy as np
import random
from level.chunk import Chunk, EMPTY, SOLID
from level.cellular_automata import get_raw_tile_array
from config import CHUNK_WIDTH_TILES, CHUNK_HEIGHT_TILES

def carve_edges(tiles: np.ndarray, entry_row: int | None = None) -> int:
    """
    makes 3 cells open on the left edge at entry_row and returns the actual entry_row used.
    """
    rows = tiles.shape[0]
    left_row = entry_row if entry_row is not None else rows // 2
    left_row = max(1, min(rows - 2, left_row))   # keep away from very top orbottom
    for r in range(left_row - 1, left_row + 2):
        tiles[r, 0] = EMPTY
    return left_row


def carve_corridor(tiles: np.ndarray, entry_row: int) -> int:
    """
    carves a guaranteed winding corridor from the left edge entry_rowto somewhere on the right edge. Moves right every step,
    driftingup or down randomly.
    """
    rows, cols = tiles.shape
    row = entry_row
    corridor_width = 3   # carve 3 cells tall so the player can fit

    for col in range(cols):
        # Carve corridor_width cells tall at this column
        for r in range(max(0, row - 1), min(rows, row + corridor_width - 1)):
            tiles[r, col] = EMPTY

        # Randomly drift up or down, bias toward staying level
        drift = random.choice([-1, -1, 0, 0, 0, 1, 1])
        row = max(1, min(rows - corridor_width - 1, row + drift))

    #right edge.....make sure the exit column is open
    exit_row = row
    for r in range(max(0, exit_row - 1), min(rows, exit_row + 2)):
        tiles[r, cols - 1] = EMPTY

    return exit_row


def generate_raw_chunk(index: int, entry_row: int | None = None) -> Chunk:
    tiles = get_raw_tile_array()
    actual_entry_row = carve_edges(tiles, entry_row)
    exit_row = carve_corridor(tiles, actual_entry_row)

    chunk = Chunk(tiles=tiles, index=index, entry_row=actual_entry_row)
    chunk.exit_row = exit_row
    return chunk