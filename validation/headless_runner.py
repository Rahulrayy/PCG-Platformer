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

    lo = cy - _HH
    hi = cy + _HH
    feet_row = int(rows - lo / _TS)

    # wall or step-up: solid tile overlapping player body in next column
    for r in range(rows):
        tb = (rows - 1 - r) * _TS
        tt = tb + _TS
        if tiles[r, next_col] == SOLID and tb < hi and tt > lo:
            return True

    # gap ahead: no solid floor within safe-drop range in next 2 columns
    for col in range(next_col, min(cols, next_col + 2)):
        has_floor = any(
            tiles[r, col] == SOLID
            for r in range(max(0, feet_row - 1),
                           min(rows, feet_row + _MAX_SAFE_DROP + 1))
        )
        if not has_floor:
            return True

    return False


_PEAK_DIST = int(_MOVE * (_JUMP / _GRAVITY))  # horizontal distance when jump arc peaks (~154px)

def run_headless(chunk: Chunk, path: list[tuple[int, int]] | None = None) -> bool:
    """
    Simulate a physics-aware bot through the chunk.
    Returns True if it reaches the right edge within _MAX_STEPS frames.
    If path (A* waypoints as (col, row) ground-tile pairs) is provided, the bot
    uses them to time elevation jumps; _should_jump handles local CA obstacles.
    """
    rows, cols = chunk.tiles.shape
    tiles = chunk.tiles

    entry_row = chunk.entry_row
    floor_row = entry_row  # entry_row is now the solid floor tile row
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

    goal_x       = (cols - 1) * _TS
    exit_floor_y = (rows - chunk.exit_row) * _TS  # floor surface at exit column
    best_x  = cx
    stuck   = 0
    wp_idx  = 1  # path[0] is the start tile, begin from next

    for _ in range(_MAX_STEPS):
        # Success: reached the right edge, on the ground, at exit floor height (±1 tile)
        if cx + _HW >= goal_x and on_ground and abs((cy - _HH) - exit_floor_y) <= _TS:
            return True

        # Advance past waypoints the bot has already reached
        if path:
            while wp_idx < len(path) - 1 and cx >= path[wp_idx][0] * _TS:
                wp_idx += 1

        vx = _MOVE

        if on_ground:
            jump = False

            # Waypoint elevation jump: jump when within peak-arc distance of a
            # higher waypoint so the arc crests at the target platform level
            if path and wp_idx < len(path):
                wp_col, wp_row = path[wp_idx]
                wp_floor_y = (rows - wp_row - 1) * _TS  # floor surface of target tile
                player_floor_y = cy - _HH
                dist_to_wp = wp_col * _TS - cx
                if wp_floor_y > player_floor_y + _TS * 0.5 and 0 < dist_to_wp <= _PEAK_DIST + _TS:
                    jump = True

            if not jump:
                jump = _should_jump(cx, cy, tiles, rows, cols)

            if jump:
                vy = _JUMP
                on_ground = False

        # Only count stuck frames when on the ground — airborne frames don't burn
        # the timeout, allowing the bot to wall-climb by rising against a wall
        if cx <= best_x + 0.5:
            if on_ground:
                stuck += 1
                if stuck >= _STUCK_STEPS:
                    return False
                if stuck % 30 == 0:
                    vy = _JUMP
                    on_ground = False
        else:
            best_x = cx
            stuck  = 0

        vy -= _GRAVITY * _DT
        if vy < -_MAX_FALL:
            vy = -_MAX_FALL

        cx += vx * _DT
        for r, c in _nearby_solid(cx, cy, tiles):
            tl, tr, tb, tt = _tile_rect(r, c, rows)
            if cx - _HW < tr and cx + _HW > tl and cy - _HH < tt and cy + _HH > tb:
                cx = tl - _HW if vx > 0 else tr + _HW
                vx = 0.0
                break

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

    return False


def record_headless(chunk: Chunk, path: list[tuple[int, int]] | None = None) -> list[tuple[float, float]]:
    """
    Same simulation as run_headless but returns a list of (cx, cy) pixel positions
    sampled every 10 steps. Returns an empty list if the bot fails to reach the exit.
    Positions are in chunk-local pixel coordinates.
    """
    rows, cols = chunk.tiles.shape
    tiles = chunk.tiles

    entry_row = chunk.entry_row
    floor_row = entry_row  # entry_row is now the solid floor tile row
    while floor_row < rows and tiles[floor_row, 0] != SOLID:
        floor_row += 1
    if floor_row >= rows:
        return []
    floor_top = (rows - floor_row) * _TS

    cx: float = _TS / 2.0
    cy: float = floor_top + _HH + 1.0
    vx: float = 0.0
    vy: float = 0.0
    on_ground = False

    goal_x       = (cols - 1) * _TS
    exit_floor_y = (rows - chunk.exit_row) * _TS
    best_x  = cx
    stuck   = 0
    wp_idx  = 1

    positions: list[tuple[float, float]] = []

    for step in range(_MAX_STEPS):
        if cx + _HW >= goal_x and on_ground and abs((cy - _HH) - exit_floor_y) <= _TS:
            return positions

        if step % 10 == 0:
            positions.append((cx, cy))

        if path:
            while wp_idx < len(path) - 1 and cx >= path[wp_idx][0] * _TS:
                wp_idx += 1

        vx = _MOVE

        if on_ground:
            jump = False
            if path and wp_idx < len(path):
                wp_col, wp_row = path[wp_idx]
                wp_floor_y = (rows - wp_row - 1) * _TS
                dist_to_wp = wp_col * _TS - cx
                if wp_floor_y > cy - _HH + _TS * 0.5 and 0 < dist_to_wp <= _PEAK_DIST + _TS:
                    jump = True
            if not jump:
                jump = _should_jump(cx, cy, tiles, rows, cols)
            if jump:
                vy = _JUMP
                on_ground = False

        if cx <= best_x + 0.5:
            if on_ground:
                stuck += 1
                if stuck >= _STUCK_STEPS:
                    return []
                if stuck % 30 == 0:
                    vy = _JUMP
                    on_ground = False
        else:
            best_x = cx
            stuck  = 0

        vy -= _GRAVITY * _DT
        if vy < -_MAX_FALL:
            vy = -_MAX_FALL

        cx += vx * _DT
        for r, c in _nearby_solid(cx, cy, tiles):
            tl, tr, tb, tt = _tile_rect(r, c, rows)
            if cx - _HW < tr and cx + _HW > tl and cy - _HH < tt and cy + _HH > tb:
                cx = tl - _HW if vx > 0 else tr + _HW
                vx = 0.0
                break

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
            return []

    return []
