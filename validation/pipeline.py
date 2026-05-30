from level.chunk import Chunk
from validation.bfs_reachability import bfs
from validation.platform_graph import PlatformGraph
from validation.headless_runner import run_headless

_graph = PlatformGraph()  # instantiated once; precomputes max_y_dict at import time

def validate(chunk: Chunk) -> bool:
    start_pos = (0, chunk.entry_row - 1)
    final_pos  = (chunk.width_tiles - 1, chunk.exit_row - 1)
    path = _graph.a_star(start_pos, final_pos, chunk.tiles, return_path=True)
    if not path:
        return False
    return run_headless(chunk, path)
