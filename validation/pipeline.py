from level.chunk import Chunk
from validation.bfs_reachability import bfs
from validation.platform_graph import PlatformGraph
from validation.headless_runner import run_headless

_graph = PlatformGraph()  # instantiated once; precomputes max_y_dict at import time

def validate(chunk: Chunk) -> bool:
    if not bfs(chunk):
        return False
    start_pos = (0, chunk.entry_row)
    final_pos  = (chunk.width_tiles - 1, chunk.exit_row)
    if not _graph.a_star(start_pos, final_pos, chunk.tiles):
        return False
    return run_headless(chunk)
