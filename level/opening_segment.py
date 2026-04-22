import numpy as np
from level.chunk import Chunk, SOLID
from config import CHUNK_WIDTH_TILES, CHUNK_HEIGHT_TILES

def make_opening_segment() -> Chunk:
    """

    no floor,falling below y=0 is death.
    everything is built around a spawn platform at row 9
    """
    tiles = np.zeros((CHUNK_HEIGHT_TILES, CHUNK_WIDTH_TILES), dtype=np.int8)
    tiles[:, 0:2] = SOLID
    tiles[9, 2:10] = SOLID
    for step in range(4):
        col_start = 12 + step * 9
        col_end   = col_start + 8
        row       = 8 - step           # rows 8- 5
        tiles[row, col_start:col_end] = SOLID


    tiles[3, 50:64]   = SOLID   #high platform after staircase
    tiles[5, 67:80]   = SOLID   # step down
    tiles[3, 83:96]   = SOLID   # back up
    tiles[5, 99:112]  = SOLID   # step down again
    tiles[7, 115:128] = SOLID   # begin descent


    for step in range(4):
        col_start = 130 + step * 7
        col_end   = col_start + 6
        row       = 8 + step           # rows 8 - 11
        tiles[row, col_start:col_end] = SOLID

    return Chunk(tiles=tiles, index=0)