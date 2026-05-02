import numpy as np
from dataclasses import dataclass
#tile type constants everything imports these.
EMPTY = 0
SOLID = 1

@dataclass
class Chunk:
    """
    One fixed-width segment of the level.
    tiles are  2d numpy array, shape (height_tiles, width_tiles).Row 0 is the TOP of the leveland row -1 is the BOTTOM.
    index  which chunk this is in the infinite sequence (0 = opening)
    """
    tiles: np.ndarray
    index: int = 0
    entry_row: int | None = None  #none until generator sets it
    exit_row: int | None = None  #none until BFS sets it
    @property
    def width_tiles(self) -> int:
        return self.tiles.shape[1]

    @property
    def height_tiles(self) -> int:
        return self.tiles.shape[0]

    def pixel_width(self, tile_size: int) -> int:
        return self.width_tiles * tile_size

    def pixel_height(self, tile_size: int) -> int:
        return self.height_tiles * tile_size