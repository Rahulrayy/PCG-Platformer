import arcade
import numpy as np
from level.chunk import Chunk, SOLID
from config import TILE_SIZE, COLOR_TILE_SOLID

def chunk_to_sprite_list(chunk: Chunk) -> arcade.SpriteList:
    walls = arcade.SpriteList(use_spatial_hash=True)

    rows, cols = chunk.tiles.shape

    for row in range(rows):
        for col in range(cols):
            if chunk.tiles[row, col] == SOLID:
                tile = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, COLOR_TILE_SOLID)
                tile.left   = col * TILE_SIZE
                tile.bottom = (rows - 1 - row) * TILE_SIZE
                walls.append(tile)

    return walls