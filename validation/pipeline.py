from level.chunk import Chunk
from validation.bfs_reachability import bfs
from validation.platform_graph import PlatformGraph
from validation.headless_runner import run_headless

_graph = PlatformGraph()  # instantiated once; precomputes max_y_dict at import time

def validate(chunk: Chunk) -> bool:
    # if not bfs(chunk):
    #     return False
    start_pos = (int(0), int(chunk.entry_row)) # type:ignore
    final_pos  = (int(chunk.width_tiles - 1), int(chunk.exit_row)) # type: ignore
    # if not _graph.a_star(start_pos, final_pos, chunk.tiles):
    #     return False
    return _graph.a_star(start_pos, final_pos, chunk.tiles)
