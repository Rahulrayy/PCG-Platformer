from collections import deque
from level.chunk import Chunk, EMPTY

def find_entry(chunk: Chunk) -> tuple[int, int] | None:
    """
    Scans the left edge top-to-bottom and returns the first empty celli f entry_row is already set on the chunk (passed from previous chunks
    exit_row) use that row directly instead of scanning.
    """
    if chunk.entry_row is not None:
        if chunk.tiles[chunk.entry_row, 0] == EMPTY:
            return (chunk.entry_row, 0)

    # backup to scan for empty space on left edge
    for row in range(chunk.height_tiles):
        if chunk.tiles[row, 0] == EMPTY:
            return (row, 0)

    return None

def bfs(chunk: Chunk) -> bool:
    entry = find_entry(chunk)
    if entry is None:
        return False

    rows  = chunk.height_tiles
    cols  = chunk.width_tiles
    right = cols - 1

    visited = set()
    queue   = deque([entry])
    visited.add(entry)

    while queue:
        row, col = queue.popleft()

        # Check if right edge reached
        if col == right:
            chunk.exit_row = row   # store for next chunks entry
            return True

        # only 4 axis check maybe upgrde to 8(diagonals) later
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if (0 <= nr < rows and 0 <= nc < cols
                    and (nr, nc) not in visited
                    and chunk.tiles[nr, nc] == EMPTY):
                visited.add((nr, nc))
                queue.append((nr, nc))

    return False   #right edge never reached