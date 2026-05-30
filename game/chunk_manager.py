import os
from concurrent.futures import ProcessPoolExecutor
import arcade
from level.chunk import Chunk
from level.tilemap import chunk_to_sprite_list
from game.chunk_worker import generate_and_validate
from config import TILE_SIZE

_N_WORKERS = min(5, max(1, (os.cpu_count() or 2) - 1))

class ChunkManager:
    """
    infinite scrool
    Rolling window keeps
      1 chunk behind  the player
       current chunk
       2 chunks ahead  the player  (preloaded before the player reaches them)

    Chunks are generated on separate processes (bypasses the GIL).
    _N_WORKERS processes race each other per chunk; first valid result wins.
    """

    KEEP_BEHIND = 1

    def __init__(self, opening_chunk: Chunk, opening_walls: arcade.SpriteList):
        self._chunk_px_width = opening_chunk.pixel_width(TILE_SIZE)

        self.walls = arcade.SpriteList(use_spatial_hash=True)

        self._loaded: dict[int, dict] = {}
        self._register_chunk(0, opening_chunk, list(opening_walls))
        for sprite in opening_walls:
            self.walls.append(sprite)

        self._current_index = 0
        self._pending: set[int] = set()
        self._futures: dict[int, list] = {}   # index -> [Future, ...]
        self._executor = ProcessPoolExecutor(max_workers=_N_WORKERS)

    def update(self, player_x: float):
        self._finalize_ready()

        self._current_index = int(player_x // self._chunk_px_width)

        # Preload the two chunks ahead as soon as prerequisites are available
        for ahead in (1, 2):
            ni = self._current_index + ahead
            if ni not in self._loaded and ni not in self._pending:
                self._schedule_chunk(ni)

        stale = [i for i in self._loaded
                 if i < self._current_index - self.KEEP_BEHIND]
        for i in stale:
            self._unload_chunk(i)

    def _finalize_ready(self):
        """main game thread only for gui."""
        to_remove = []
        for index, futures in self._futures.items():
            done_futures = [f for f in futures if f.done()]
            if not done_futures:
                continue

            # Check if any finished worker found a valid chunk
            chunk, attempt = None, None
            for f in done_futures:
                try:
                    c, a = f.result()
                    if c is not None and chunk is None:
                        chunk, attempt = c, a
                except Exception as e:
                    import traceback
                    print(f"[chunk {index}] EXCEPTION in worker: {e}")
                    traceback.print_exc()

            if chunk is not None:
                to_remove.append(index)
                for f in futures:
                    f.cancel()
                self._pending.discard(index)
                if index not in self._loaded:
                    print(f"[chunk {index}] passed validation on attempt {attempt}")
                    offset_x = index * self._chunk_px_width
                    raw_walls = chunk_to_sprite_list(chunk)
                    sprites = []
                    for sprite in raw_walls:
                        sprite.left += offset_x
                        self.walls.append(sprite)
                        sprites.append(sprite)
                    self._register_chunk(index, chunk, sprites)
            elif all(f.done() for f in futures):
                to_remove.append(index)
                self._pending.discard(index)
                print(f"[chunk {index}] validate failed all attempts")

        for index in to_remove:
            self._futures.pop(index, None)

    def _schedule_chunk(self, index: int):
        prev = self._loaded.get(index - 1, {}).get('chunk')
        if prev is None and index > 0:
            return   # prerequisite not loaded yet; update() will retry next frame
        entry = prev.exit_row if prev else None
        self._pending.add(index)
        self._futures[index] = [
            self._executor.submit(generate_and_validate, index, entry)
            for _ in range(_N_WORKERS)
        ]

    @property
    def world_pixel_width(self) -> int:
        """Right edge of the furthest loaded chunk used to clamp the camera"""
        if not self._loaded:
            return self._chunk_px_width
        return (max(self._loaded.keys()) + 1) * self._chunk_px_width

    def _register_chunk(self, index: int, chunk: Chunk, sprites: list):
        self._loaded[index] = {'chunk': chunk, 'sprites': sprites}

    def _unload_chunk(self, index: int):
        if index not in self._loaded:
            return
        for sprite in self._loaded[index]['sprites']:
            self.walls.remove(sprite)
        del self._loaded[index]
