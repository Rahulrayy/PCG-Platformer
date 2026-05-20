import numpy as np
import random
from level.chunk import Chunk, EMPTY, SOLID
from level.cellular_automata import get_raw_tile_array
from config import CHUNK_WIDTH_TILES, CHUNK_HEIGHT_TILES

_CORRIDOR_WIDTH = 4  # change to 4 to avoid hitting head onn juumping archs


def carve_edges(tiles: np.ndarray, entry_row: int | None = None) -> int:
    rows = tiles.shape[0]
    left_row = entry_row if entry_row is not None else rows // 2
    left_row = max(1, min(rows - _CORRIDOR_WIDTH - 1, left_row))
    for r in range(left_row - 1, min(rows, left_row + _CORRIDOR_WIDTH - 1)):
        tiles[r, 0] = EMPTY
    floor_r = left_row + _CORRIDOR_WIDTH - 1
    if floor_r < rows:
        tiles[floor_r, 0] = SOLID   # entry ground node for A*
    return left_row


def carve_corridor(tiles: np.ndarray, entry_row: int) -> int:
    rows, cols = tiles.shape
    row = entry_row

    for col in range(cols):
        for r in range(max(0, row - 1), min(rows, row + _CORRIDOR_WIDTH - 1)):
            tiles[r, col] = EMPTY

        drift = random.choice([-1, -1, 0, 0, 0, 1, 1])
        row = max(1, min(rows - _CORRIDOR_WIDTH - 1, row + drift))

    exit_row = row
    for r in range(max(0, exit_row - 1), min(rows, exit_row + _CORRIDOR_WIDTH - 1)):
        tiles[r, cols - 1] = EMPTY
    floor_r = exit_row + _CORRIDOR_WIDTH - 1
    if floor_r < rows:
        tiles[floor_r, cols - 1] = SOLID   # exit ground node for A*
    return exit_row


def generate_raw_chunk(index: int, entry_row: int | None = None) -> Chunk:
    tiles = get_raw_tile_array()
    actual_entry_row = carve_edges(tiles, entry_row)
    exit_row = carve_corridor(tiles, actual_entry_row)

    chunk = Chunk(tiles=tiles, index=index, entry_row=actual_entry_row)
    chunk.exit_row = exit_row
    return chunk
