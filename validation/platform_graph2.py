import config
import numpy as np
import heapq as hp

# Physics constants (same as headless_runner)
_TS       = config.TILE_SIZE
_HW       = 10
_HH       = 12
_GRAVITY  = config.GRAVITY
_JUMP     = config.JUMP_SPEED
_MOVE     = config.MOVE_SPEED
_MAX_FALL = config.MAX_FALL_SPEED
_DT       = 1.0 / 60.0
_MAX_SIM_STEPS = 300   # 5 seconds at 60 fps – enough for most jumps

class Node:
    def __init__(self, parent, pos, g, h):
        self.x = pos[0]
        self.y = pos[1]
        self.pos = pos
        self.parent = parent
        self.g = g
        self.h = h

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.x == other.x and self.y == other.y

    def __lt__(self, other):
        return (self.g + self.h) < (other.g + other.h)

    def __hash__(self):
        return hash(self.pos)


class PlatformGraph:
    def __init__(self):
        self.v_jump = config.JUMP_SPEED
        self.g = config.GRAVITY
        self.v_x = config.MOVE_SPEED
        self.v_max = config.MAX_FALL_SPEED
        self.t_max  = (self.v_jump + self.v_max) / self.g
        self.t_rise = self.v_jump / self.g
        self.peak_px = int(self.v_x * self.t_rise)

        self.screen_width = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT
        self.screen_shape = (config.SCREEN_HEIGHT, config.SCREEN_WIDTH)

        # Precompute max_y for all dx (pixel offsets)
        self.max_y_dict = {}
        self.calc_max_y(np.arange(self.screen_width))
        self._max_y_arr = np.array([self.max_y_dict[d] for d in range(self.screen_width)])

    def calc_max_y(self, arr_x):
        for xi in arr_x:
            max_y = self._max_y(dx=xi)
            self.max_y_dict[xi] = max_y

    def _max_y(self, dx: int) -> int:
        t1 = dx / self.v_x
        if t1 <= self.t_max:
            y_max = self.v_jump * t1 - (self.g * (t1 ** 2)) / 2
        else:
            y_max = self.v_jump * self.t_max - (self.g * (self.t_max ** 2)) / 2 - self.v_max * (t1 - self.t_max)
        return int(y_max)

    def _reachable(self, pos1: tuple[int, int], grid_shape: tuple[int, int]):
        y_coords, x_coords = np.indices(grid_shape)
        dx = x_coords - pos1[0]
        dx_px = dx * config.TILE_SIZE

        min_px = max(int(np.min(dx_px)), 0)
        max_px = min(int(np.max(dx_px)), self.screen_width - 1)
        max_y_lookup = self._max_y_arr[min_px:max_px + 1]
        lookup_indices = np.clip(dx_px, min_px, max_px) - min_px
        max_y_values = max_y_lookup[lookup_indices] / config.TILE_SIZE
        reachable_mask = y_coords >= (pos1[1] - max_y_values)
        return reachable_mask

    def _is_ground(self, chunk: np.ndarray):
        ground_diff = np.zeros_like(chunk)
        ground_diff[1:, :a] = chunk[1:, :] - chunk[:-1, :]
        ground_mask = np.where(ground_diff == 1)
        return ground_mask

    def _arc_clear(self, pos1: tuple[int, int], pos2: tuple[int, int], chunk: np.ndarray) -> bool:
        """Original analytic arc clearance check."""
        for col in range(pos1[0] + 1, pos2[0]):
            t = (col - pos1[0]) * config.TILE_SIZE / self.v_x
            if t <= self.t_max:
                y_offset_px = self.v_jump * t - (self.g * t ** 2) / 2
            else:
                y_offset_px = self.v_jump * self.t_max - (self.g * self.t_max ** 2) / 2 - self.v_max * (t - self.t_max)
            arc_row = pos1[1] - y_offset_px / config.TILE_SIZE
            for row in [int(arc_row), int(arc_row) - 1]:
                if 0 <= row < chunk.shape[0] and chunk[row, col] == 1:
                    return False
        return True

    # ------------------------------------------------------------------
    # Physics verification for edges that fail analytic check
    # ------------------------------------------------------------------
    def _verify_with_physics(self, start_tile: tuple[int, int], target_tile: tuple[int, int],
                             chunk: np.ndarray) -> bool:
        """
        Simulate a jump from start_tile, allowing the player to stop moving right
        mid‑air to avoid obstacles or overshoot. Returns True if we can land exactly
        on target_tile.
        """
        rows, cols = chunk.shape
        # Initial pixel position (center of start tile, feet on ground)
        cx = start_tile[0] * _TS + _TS//2
        start_row = start_tile[1]
        tile_top_px = (rows - start_row) * _TS
        cy = tile_top_px + _HH

        vx = _MOVE      # start moving right
        vy = _JUMP      # immediate jump
        on_ground = True   # we start on ground, then jump

        target_col = target_tile[0]
        target_row = target_tile[1]

        # Helper: get nearby solid tiles (same as headless_runner)
        def nearby_solid(cx, cy):
            col_lo = max(0, int((cx - _HW) // _TS) - 1)
            col_hi = min(cols - 1, int((cx + _HW) // _TS) + 1)
            r_lo = max(0, int(rows - 1 - (cy + _HH) // _TS) - 1)
            r_hi = min(rows - 1, int(rows - 1 - (cy - _HH) // _TS) + 1)
            for r in range(r_lo, r_hi + 1):
                for c in range(col_lo, col_hi + 1):
                    if chunk[r, c] == 1:
                        yield r, c

        def tile_rect(r, c):
            left = c * _TS
            right = left + _TS
            bottom = (rows - 1 - r) * _TS
            top = bottom + _TS
            return left, right, bottom, top

        for step in range(_MAX_SIM_STEPS):
            # ---- Horizontal control ----
            # If we have already passed the target column, stop moving right
            if cx + _HW > target_col * _TS:
                vx = 0
            else:
                # Simple look‑ahead: if moving right would cause a collision, stop
                test_cx = cx + vx * _DT
                collision = False
                for r, c in nearby_solid(test_cx, cy):
                    l, r_px, b, t = tile_rect(r, c)
                    if test_cx - _HW < r_px and test_cx + _HW > l and cy - _HH < t and cy + _HH > b:
                        collision = True
                        break
                if collision:
                    vx = 0
                else:
                    vx = _MOVE

            # ---- Horizontal movement + collision ----
            cx += vx * _DT
            for r, c in nearby_solid(cx, cy):
                l, r_px, b, t = tile_rect(r, c)
                if cx - _HW < r_px and cx + _HW > l and cy - _HH < t and cy + _HH > b:
                    cx = l - _HW if vx > 0 else r_px + _HW
                    vx = 0.0
                    break

            # ---- Vertical movement + collision ----
            cy += vy * _DT
            on_ground = False
            for r, c in nearby_solid(cx, cy):
                l, r_px, b, t = tile_rect(r, c)
                if cx - _HW < r_px and cx + _HW > l and cy - _HH < t and cy + _HH > b:
                    if vy <= 0:
                        cy = t + _HH
                        on_ground = True
                    else:
                        cy = b - _HH
                    vy = 0.0
                    break

            # ---- Gravity ----
            vy -= _GRAVITY * _DT
            if vy < -_MAX_FALL:
                vy = -_MAX_FALL

            # ---- Check landing ----
            if on_ground and step > 0:
                bottom_y = cy - _HH
                row = rows - 1 - int(bottom_y // _TS)
                col = int(cx // _TS)
                if 0 <= col < cols and 0 <= row < rows and chunk[row, col] == 1:
                    landed = (col, row)
                    if landed == target_tile:
                        return True
                    else:
                        return False   # landed on wrong tile
            # Out of bounds
            if cy + _HH < 0 or cy - _HH > rows * _TS:
                return False

        return False

    # ------------------------------------------------------------------
    # Manhattan heuristic
    # ------------------------------------------------------------------
    def manhattan_dist(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # ------------------------------------------------------------------
    # A* with hybrid verification
    # ------------------------------------------------------------------
    def a_star(self, start_pos, final_pos, chunk, return_path: bool = False):
        start_node = Node(None, start_pos, 0, self.manhattan_dist(start_pos, final_pos))
        open_queue = [(start_node.g + start_node.h, start_node)]
        hp.heapify(open_queue)
        open_set = {start_node}
        closed_set = set()

        ground_rows, ground_cols = self._is_ground(chunk)
        child_positions = [(int(c), int(r)) for r, c in zip(ground_rows, ground_cols)]
        if not child_positions:
            return [] if return_path else False
        _gx = np.array([p[0] for p in child_positions])
        _gy = np.array([p[1] for p in child_positions])

        # Cache for verification results
        verify_cache = {}

        while open_queue:
            score, node = hp.heappop(open_queue)
            if node.pos in closed_set:
                open_set.discard(node)
                continue

            # Goal test: any ground tile on the final column
            if node.x == final_pos[0]:
                if return_path:
                    path = []
                    n = node
                    while n:
                        path.append(n.pos)
                        n = n.parent
                    path.reverse()
                    return path
                return True

            open_set.discard(node)
            closed_set.add(node.pos)

            reachable_mask = self._reachable(node.pos, chunk.shape)
            reachable_flags = reachable_mask[_gy, _gx]

            for i in np.where(reachable_flags)[0]:
                pos = child_positions[i]   # candidate ground tile
                if pos in closed_set:
                    continue

                # Only consider moves to the right (x increasing)
                if pos[0] <= node.x:
                    continue

                # ---- Upward jump? (target row < current row) ----
                if pos[1] < node.pos[1]:
                    dx_px = (pos[0] - node.pos[0]) * config.TILE_SIZE
                    # Still rising? Cannot land
                    if dx_px < self.peak_px:
                        continue
                    # Analytic arc clear?
                    if self._arc_clear(node.pos, pos, chunk):
                        # Valid by analytic method
                        g = node.g + self.manhattan_dist(node.pos, pos)
                        h = self.manhattan_dist(pos, final_pos)
                        child = Node(node, pos, g, h)
                        if child not in open_set:
                            open_set.add(child)
                            hp.heappush(open_queue, (g + h, child))
                    else:
                        # Analytic says impossible – try physics verification
                        key = (node.pos, pos)
                        if key not in verify_cache:
                            verify_cache[key] = self._verify_with_physics(node.pos, pos, chunk)
                        if verify_cache[key]:
                            g = node.g + self.manhattan_dist(node.pos, pos)
                            h = self.manhattan_dist(pos, final_pos)
                            child = Node(node, pos, g, h)
                            if child not in open_set:
                                open_set.add(child)
                                hp.heappush(open_queue, (g + h, child))
                else:
                    # ---- Downward or level move ----
                    # For non‑adjacent downward moves, also try verification if needed
                    # But original code didn't check arcs here. We'll just accept analytic mask.
                    # However you can add a similar verification for tricky downward falls.
                    # For simplicity, we accept all such moves (they are usually safe).
                    g = node.g + self.manhattan_dist(node.pos, pos)
                    h = self.manhattan_dist(pos, final_pos)
                    child = Node(node, pos, g, h)
                    if child not in open_set:
                        open_set.add(child)
                        hp.heappush(open_queue, (g + h, child))

        return [] if return_path else False