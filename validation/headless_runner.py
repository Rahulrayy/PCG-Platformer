import config
from level.chunk import Chunk, SOLID

_TS       = config.TILE_SIZE
_HW       = 10     # player half-width
_HH       = 12     # player half-height
_GRAVITY  = config.GRAVITY
_JUMP     = config.JUMP_SPEED
_MOVE     = config.MOVE_SPEED
_MAX_FALL = config.MAX_FALL_SPEED
_DT       = 1.0 / 60.0
_MAX_STEPS   = 3000
_STUCK_STEPS = 300
_MAX_SAFE_DROP = 2


def _tile_rect(r: int, c: int, rows: int):
    left   = c * _TS
    bottom = (rows - 1 - r) * _TS
    return left, left + _TS, bottom, bottom + _TS


def _nearby_solid(cx: float, cy: float, tiles):
    rows, cols = tiles.shape
    col_lo = max(0,        int((cx - _HW) // _TS) - 1)
    col_hi = min(cols - 1, int((cx + _HW) // _TS) + 1)
    r_lo   = max(0,        int(rows - 1 - (cy + _HH) // _TS) - 1)
    r_hi   = min(rows - 1, int(rows - 1 - (cy - _HH) // _TS) + 1)
    for r in range(r_lo, r_hi + 1):
        for c in range(col_lo, col_hi + 1):
            if tiles[r, c] == SOLID:
                yield r, c


def _should_jump(cx: float, cy: float, tiles, rows: int, cols: int) -> bool:
    next_col = int((cx + _HW) / _TS) + 1
    if next_col >= cols:
        return False

    lo = cy - _HH   # player bottom in pixels
    hi = cy + _HH   # player top  in pixels

    #wall/ step-up----solid tile in next column overlaps player body
    for r in range(rows):
        tb = (rows - 1 - r) * _TS
        tt = tb + _TS
        if tiles[r, next_col] == SOLID and tb < hi and tt > lo:
            return True

    #no solid floor within the safe-drop range in the next 2 columns
    feet_row = int(rows - lo / _TS)
    for col in range(next_col, min(cols, next_col + 2)):
        has_floor = any(
            tiles[r, col] == SOLID
            for r in range(max(0, feet_row - 1),
                           min(rows, feet_row + _MAX_SAFE_DROP + 1))
        )
        if not has_floor:
            return True

    return False


def run_headless(chunk: Chunk) -> bool:
    """
    Simulate a physics-aware bot through the chunk.
    Returns True if it reaches the right edge within _MAX_STEPS frames.
    """
    rows, cols = chunk.tiles.shape
    tiles = chunk.tiles

    # Start just above the guaranteed floor tile at column 0
    entry_row = chunk.entry_row
    floor_row = entry_row + 1
    while floor_row < rows and tiles[floor_row, 0] != SOLID:
        floor_row += 1
    if floor_row >= rows:
        return False
    floor_top = (rows - floor_row) * _TS

    cx: float = _TS / 2.0
    cy: float = floor_top + _HH + 1.0
    vx: float = 0.0
    vy: float = 0.0
    on_ground = False

    goal_x = (cols - 1) * _TS
    best_x  = cx
    stuck   = 0

    for _ in range(_MAX_STEPS):
        if cx + _HW >= goal_x:
            return True

        #Bot input-- always move right, jump only when the look-ahead says to
        vx = _MOVE
        if on_ground and _should_jump(cx, cy, tiles, rows, cols):
            vy = _JUMP
            on_ground = False

        #ggravity
        vy -= _GRAVITY * _DT
        if vy < -_MAX_FALL:
            vy = -_MAX_FALL

        #horizontal move + collision resolution
        cx += vx * _DT
        for r, c in _nearby_solid(cx, cy, tiles):
            tl, tr, tb, tt = _tile_rect(r, c, rows)
            if cx - _HW < tr and cx + _HW > tl and cy - _HH < tt and cy + _HH > tb:
                cx = tl - _HW if vx > 0 else tr + _HW
                vx = 0.0
                break

        #Vertical move + collision resolution
        on_ground = False
        cy += vy * _DT
        for r, c in _nearby_solid(cx, cy, tiles):
            tl, tr, tb, tt = _tile_rect(r, c, rows)
            if cx - _HW < tr and cx + _HW > tl and cy - _HH < tt and cy + _HH > tb:
                if vy <= 0:
                    cy = tt + _HH
                    on_ground = True
                else:
                    cy = tb - _HH
                vy = 0.0
                break


        if cy + _HH < 0:
            return False


    return True
