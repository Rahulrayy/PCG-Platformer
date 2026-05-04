import threading
import queue as _queue
import arcade
from level.chunk import Chunk
from level.tilemap import chunk_to_sprite_list
from level.generator import generate_raw_chunk
from validation.bfs_reachability import bfs
from config import TILE_SIZE

class ChunkManager:
    """
    infinite scrool
    Rolling window keeps
      1 chunk behind  the player
       current chunk
       1 chunk ahead   the player  (preloaded before the player reaches it)

    chunks is now generated on a background thread.
    """

    LOOKAHEAD_PX  = 20 * TILE_SIZE
    KEEP_BEHIND   = 1

    def __init__(self, opening_chunk: Chunk, opening_walls: arcade.SpriteList):
        self._chunk_px_width = opening_chunk.pixel_width(TILE_SIZE)

        self.walls = arcade.SpriteList(use_spatial_hash=True)

        # Chunk 0 sprites sit at world offset 0
        self._loaded: dict[int, dict] = {}
        self._register_chunk(0, opening_chunk, list(opening_walls))
        for sprite in opening_walls:
            self.walls.append(sprite)

        self._current_index = 0
        self._pending: set[int] = set()           # gen indies on a diff thered
        self._ready: _queue.Queue = _queue.Queue() # (index, chunk  from workers

    def update(self, player_x: float):
        # Finalize any chunks whose background generation finished
        self._finalize_ready()

        self._current_index = int(player_x // self._chunk_px_width)

        # Preload the chunk ahead if not already loaded or in flight
        next_index = self._current_index + 1
        if next_index not in self._loaded and next_index not in self._pending:
            right_edge = (self._current_index + 1) * self._chunk_px_width
            if player_x > right_edge - self.LOOKAHEAD_PX:
                self._schedule_chunk(next_index)

        # Unload chunks that are too far behind
        stale = [i for i in self._loaded
                 if i < self._current_index - self.KEEP_BEHIND]
        for i in stale:
            self._unload_chunk(i)

    def _finalize_ready(self):
        """main game thread only for gui."""
        while True:
            try:
                index, chunk = self._ready.get_nowait()
            except _queue.Empty:
                break
            self._pending.discard(index)
            if chunk is None or index in self._loaded:
                continue
            offset_x  = index * self._chunk_px_width
            raw_walls = chunk_to_sprite_list(chunk)
            sprites = []
            for sprite in raw_walls:
                sprite.left += offset_x
                self.walls.append(sprite)
                sprites.append(sprite)
            self._register_chunk(index, chunk, sprites)

    def _schedule_chunk(self, index: int):
        prev = self._loaded.get(index - 1, {}).get('chunk')
        if prev is None and index > 0:
            return
        entry = prev.exit_row if prev else None
        self._pending.add(index)
        threading.Thread(
            target=self._generate_worker,
            args=(index, entry),
            daemon=True,
        ).start()

    def _generate_worker(self, index: int, entry_row):
        result = None
        for _ in range(20):
            chunk = generate_raw_chunk(index=index, entry_row=entry_row)
            if bfs(chunk):
                result = chunk
                break
        self._ready.put((index, result))

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