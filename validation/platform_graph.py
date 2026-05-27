import config
import math
import heapq as hp
import numpy as np


class Node:
    """
    Search state: tile position + vertical velocity.

    Velocity is rounded to the nearest px/s so that floating-point noise does
    not fragment physically identical states into distinct nodes.
    """

    def __init__(self, parent, pos: tuple[int, int], vy: float, g_cost: float, h_cost: float):
        self.pos    = pos       # (col, row) in tile space
        self.vy     = vy        # vertical velocity px/s — positive means upward
        self.parent = parent
        self.g      = g_cost
        self.h      = h_cost

    def state(self) -> tuple:
        """Canonical key used for closed-set membership and cost tracking."""
        return (self.pos, round(self.vy))   # round to 1 px/s bins

    def __eq__(self, other):
        return isinstance(other, Node) and self.state() == other.state()

    def __hash__(self):
        return hash(self.state())

    def __lt__(self, other):
        return (self.g + self.h) < (other.g + other.h)


class PlatformGraph:
    """
    A* pathfinder that encodes physics state (position + vertical velocity)
    directly into each node.

    Neighbour generation simulates one tile-column of movement at a time,
    so there is no need for precomputed reachability tables (_reachable /
    max_y_dict) or separate arc-clearance passes (_arc_clear).  Walking off
    a ledge is handled naturally: from a ground tile the character can either
    jump (vy = JUMP_SPEED) or walk (vy = 0); gravity takes over as soon as
    there is no floor in the next column.

    Horizontal actions each step: move left (dx = -1), stand still (dx = 0),
    move right (dx = +1).  'dt' is fixed as TILE_SIZE / MOVE_SPEED regardless
    of whether the character actually moves horizontally — standing still simply
    means one dt elapses while the column stays the same.  This lets the
    character jump straight up to reach platforms directly above.
    """

    def __init__(self):
        self.v_jump  = config.JUMP_SPEED
        self.g_accel = config.GRAVITY
        self.v_x     = config.MOVE_SPEED
        self.v_max   = config.MAX_FALL_SPEED
        self.tile    = config.TILE_SIZE

        self.screen_width  = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT

        # Time the character spends crossing a single tile column
        self.dt = self.tile / self.v_x

    # ------------------------------------------------------------------ #
    #  Physics primitives                                                   #
    # ------------------------------------------------------------------ #

    def _step_vy(self, vy: float) -> float:
        """Apply one tick of gravity, clamped to terminal (downward) velocity."""
        return max(vy - self.g_accel * self.dt, -self.v_max)

    def _row_after_step(self, row: int, vy: float) -> float:
        """
        Fractional tile row after crossing one column with initial upward velocity vy.
        Rows increase downward, so positive dy_px (upward motion) lowers the row index.
        """
        dy_px = vy * self.dt - 0.5 * self.g_accel * self.dt ** 2
        return row - dy_px / self.tile

    def _solid(self, col: int, row: int, chunk: np.ndarray) -> bool:
        r, c = int(row), int(col)
        return 0 <= r < chunk.shape[0] and 0 <= c < chunk.shape[1] and chunk[r, c] == 1

    def _on_ground(self, col: int, row: int, chunk: np.ndarray) -> bool:
        """Current tile is empty and the tile directly below is solid."""
        return not self._solid(col, row, chunk) and self._solid(col, row + 1, chunk)

    def _sweep_clear(self, col: int, row_src: float, row_dst: float, chunk: np.ndarray) -> bool:
        """
        Sweep column `col` between row_src and row_dst.
        Returns False if any solid tile lies in the swept range, preventing
        the character from tunnelling through thin floors or ceilings.
        """
        r_lo = int(math.floor(min(row_src, row_dst)))
        r_hi = int(math.ceil (max(row_src, row_dst)))
        for r in range(max(r_lo, 0), min(r_hi + 1, chunk.shape[0])):
            if chunk[r, col] == 1:
                return False
        return True

    # ------------------------------------------------------------------ #
    #  Neighbour expansion                                                  #
    # ------------------------------------------------------------------ #

    def _neighbours(self, node: Node, chunk: np.ndarray):
        """
        Yield (child_pos, child_vy) pairs reachable in one time step (dt).

        Horizontal actions
        ------------------
        dx = -1  move left  — new_col = col - 1
        dx =  0  stand still — new_col = col; one dt passes, vertical physics applies
        dx = +1  move right  — new_col = col + 1

        Vertical actions (combined with any horizontal choice)
        -------------------------------------------------------
        On ground → walk/idle  : vy stays 0; character falls if no floor below new_col.
        On ground → jump       : vy is set to JUMP_SPEED.
        In the air             : only the current vy continues (no mid-air jumps).

        Standing still on solid ground (vy=0 → vy=0, same tile) is detected and
        skipped because it is never part of an optimal path and would pollute the heap.
        """
        col, row = node.pos
        on_ground = self._on_ground(col, row, chunk)

        vy_starts = [node.vy]
        if on_ground:
            vy_starts.append(self.v_jump)   # jump is an extra action from ground

        for dx in (-1, 0, 1):
            new_col = col + dx
            if not (0 <= new_col < chunk.shape[1]):
                continue

            for vy0 in vy_starts:
                new_row_f = self._row_after_step(row, vy0)
                new_row   = int(round(new_row_f))

                if not (0 <= new_row < chunk.shape[0]):
                    continue                         # out of bounds vertically

                if self._solid(new_col, new_row, chunk):
                    continue                         # destination tile is solid

                # For dx=0: sweep the current column for ceilings/floors between
                # current row and new row (handles jumping straight up, falling in place).
                # For dx!=0: sweep the destination column as before.
                if not self._sweep_clear(new_col, row, new_row_f, chunk):
                    continue                         # arc passes through a wall/floor

                new_vy = self._step_vy(vy0)

                if self._on_ground(new_col, new_row, chunk):
                    new_vy = 0.0                     # landed — reset vertical velocity

                # Skip the trivial no-op: standing still on the ground changes nothing
                if (new_col, new_row) == node.pos and new_vy == node.vy:
                    continue

                yield (new_col, new_row), new_vy

    # ------------------------------------------------------------------ #
    #  Heuristic                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _manhattan(pos1: tuple, pos2: tuple) -> int:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # ------------------------------------------------------------------ #
    #  A* search                                                            #
    # ------------------------------------------------------------------ #

    def a_star(self, start_pos: tuple[int, int], final_pos: tuple[int, int], chunk: np.ndarray) -> bool:
        """
        Return True if a physics-valid path from start_pos to the column of
        final_pos exists, False otherwise.
        """
        col0, row0 = start_pos
        # If the start position is already airborne, give it a small initial
        # downward velocity (one gravity tick from rest) rather than zero.
        start_vy = 0.0 if self._on_ground(col0, row0, chunk) else self._step_vy(0.0)

        start = Node(
            parent = None,
            pos    = start_pos,
            vy     = start_vy,
            g_cost = 0,
            h_cost = self._manhattan(start_pos, final_pos),
        )

        open_pq: list               = [(start.g + start.h, start)]
        best_g:  dict[tuple, float] = {start.state(): 0.0}
        closed:  set[tuple]         = set()

        while open_pq:
            _, node = hp.heappop(open_pq)
            state   = node.state()

            if state in closed:
                continue
            closed.add(state)

            if node.pos[0] == final_pos[0]:     # reached the target column
                return True

            for child_pos, child_vy in self._neighbours(node, chunk):
                child_g = node.g + self._manhattan(node.pos, child_pos)
                child   = Node(
                    parent = node,
                    pos    = child_pos,
                    vy     = child_vy,
                    g_cost = child_g,
                    h_cost = self._manhattan(child_pos, final_pos),
                )
                cstate = child.state()

                if cstate in closed:
                    continue

                # Only push if this is the cheapest known route to this state
                if cstate not in best_g or child_g < best_g[cstate]:
                    best_g[cstate] = child_g
                    hp.heappush(open_pq, (child_g + child.h, child))

        return False