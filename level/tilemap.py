import arcade
import numpy as np
from level.chunk import Chunk, SOLID
from config import TILE_SIZE

def chunk_to_sprite_list(chunk: Chunk) -> arcade.SpriteList:
    walls = arcade.SpriteList(use_spatial_hash=True)
    
    tileset = arcade.load_spritesheet(
        "PCG-Platformer\\assets\\Tileset.png",
        sprite_width=48,
        sprite_height=48,
        columns=3,
        count=9
    )

    rows, cols = chunk.tiles.shape
    for row in range(rows):
        for col in range(cols):
            if chunk.tiles[row, col] == SOLID:
                tile = arcade.Sprite()
                tile.texture = tileset[0] 
                tile.scale = TILE_SIZE / 45
                tile.left = col * TILE_SIZE
                tile.bottom = (rows - 1 - row) * TILE_SIZE
                walls.append(tile)
    return walls