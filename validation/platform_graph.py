import config 
import numpy as np
import heapq as hp

class Node:
    def __init__(self, parent, pos, g, h):
        self.x = pos[0]
        self.y = pos[1]
        self.pos = pos
        self.parent = parent
        self.g = g
        self.h = h


    def __eq__(self, other):
        assert isinstance(other, Node), "Can only compare nodes with each other"
        if other.x == self.x and other.y == self.y:
            return True
        return False

    def __lt__(self, other):
        return (self.g + self.h) < (other.g + other.h)

    def __hash__(self):
        return hash(self.pos)



class PlatformGraph():
    """Class will generate a graph from using the game physics and the map"""

    def __init__(self):
        self.v_jump = config.JUMP_SPEED
        self.g = config.GRAVITY
        self.v_x = config.MOVE_SPEED
        self.v_max = config.MAX_FALL_SPEED
        self.t_max  = (self.v_jump + self.v_max) / self.g
        self.t_y_max = self.v_jump / self.g
        self.t_rise = self.v_jump / self.g                  # time to arc peak
        self.peak_px = int(self.v_x * self.t_rise)          # horizontal distance at arc peak

        self.screen_width = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT
        self.screen_shape = (config.SCREEN_HEIGHT, config.SCREEN_WIDTH)

        # Pre calculates all the possible
        self.max_y_dict = {}
        self.calc_max_y(np.arange(self.screen_width))
        # flat array version for O(1) slice in _reachable instead of per-call dict rebuild
        self._max_y_arr = np.array([self.max_y_dict[d] for d in range(self.screen_width)])

    def calc_max_y(self, arr_x):
        for xi in arr_x:
            max_y = self._max_y(dx=xi)
            self.max_y_dict[xi] = max_y

    def _max_y(self, dx: int) -> int:
        """Possibly pre compute all the possible dx, dy combinations to save computational cost"""
        t1 = dx / self.v_x
        
        maximum_y = self.v_jump * self.t_y_max - (self.g * (self.t_y_max ** 2)) / 2 # This is the maximum height that can be reached independant of dt

        if t1 <= self.t_y_max and t1 > 0: # If the character is still ascending, you can reach uptill the maximum height
            y_max = maximum_y

        elif t1 <= self.t_max:
            y_max = self.v_jump * t1 - (self.g * (t1 ** 2)) / 2 # fall is parabolic if t1 <= t_max

        else:
            y_max = self.v_jump * self.t_max - (self.g * (self.t_max ** 2)) / 2 - self.v_max * (t1 - self.t_max) # fall becomes linear after t1 > t_max
    
        return int(y_max)
    
    def _reachable(self, pos1: tuple[int, int], grid_shape: tuple[int, int]):
        y_coords, x_coords = np.indices(grid_shape)
        dx = x_coords - pos1[0]
        dx_px = dx * config.TILE_SIZE  # ositions are in tiles; physics dict is keyed in pixels

        min_px = max(int(np.min(dx_px)), 0)                     # negative dx (leftward) not in dict, default 0
        max_px = min(int(np.max(dx_px)), self.screen_width - 1) #clamp to precomputed range
        max_y_lookup = self._max_y_arr[min_px:max_px + 1]
        lookup_indices = np.clip(dx_px, min_px, max_px) - min_px  # clip before indexing to avoid negatives
        max_y_values = max_y_lookup[lookup_indices] / config.TILE_SIZE  #convert pixel height back to tiles
        reachable_mask = y_coords >= (pos1[1] - max_y_values) # row 0 is top so jumping up = decreasing row
        return reachable_mask

    def _is_ground(self, chunk: np.ndarray):
        ground_diff = chunk[1:, :] - chunk[:-1, :] # 1 where empty tile has solid tile directly below
        ground_mask = np.where(ground_diff == 1)
        return ground_mask
    
    def _arc_clear(self, pos1: tuple[int, int], pos2: tuple[int, int], chunk: np.ndarray) -> bool:
        """Returns False if a solid tile blocks the jump arc between pos1 and pos2."""
        for col in range(pos1[0] + 1, pos2[0]):
            t = (col - pos1[0]) * config.TILE_SIZE / self.v_x
            if t <= self.t_max:
                y_offset_px = self.v_jump * t - (self.g * t ** 2) / 2
            else:
                y_offset_px = self.v_jump * self.t_max - (self.g * self.t_max ** 2) / 2 - self.v_max * (t - self.t_max)
            arc_row = pos1[1] - y_offset_px / config.TILE_SIZE  # up = decreasing row
            for row in [int(arc_row), int(arc_row) - 1]:  # check feet and head (player is 1 tile tall)
                if 0 <= row < chunk.shape[0] and chunk[row, col] == 1:
                    return False
        return True

    def manhatten_dist(self, pos1, pos2):
        return np.sum(np.abs(np.array(pos1) - np.array(pos2)))

    def a_star(self, start_pos, final_pos, chunk, return_path: bool = False):
        """Will check from start position all possible nodes it can expand......it will iteratively keep expanding the nodes untill it has found exit or not able to expand further."""

        start_node = Node(None, start_pos, 0, self.manhatten_dist(start_pos, final_pos))

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

        while open_queue:
            score, node = hp.heappop(open_queue)

            if node.pos in closed_set:
                open_set.discard(node)  # remove stale duplicate so open_set stays accurate
                continue

            if node.x == final_pos[0]:  # any ground tile on the right edge column is a valid exit
                if return_path:
                    path = []
                    n = node
                    while n is not None:
                        path.append(n.pos)
                        n = n.parent
                    path.reverse()
                    return path
                return True

            open_set.discard(node)
            closed_set.add(node.pos)

            reachable_mask = self._reachable(node.pos, chunk.shape)
            # vectorised: index the mask at all ground positions in one shot, iterate only reachable ones
            reachable_flags = reachable_mask[_gy, _gx]

            for i in np.where(reachable_flags)[0]:
                pos = child_positions[i]
                if pos in closed_set:
                    continue
                if pos[1] < node.pos[1]:  # upward jump
                    dx_px = (pos[0] - node.pos[0]) * config.TILE_SIZE
                    # adjacent 1-tile step: player wall-climbs, no arc constraint applies
                    adjacent_step = (node.pos[1] - pos[1] == 1 and pos[0] == node.pos[0] + 1)
                    if not adjacent_step and dx_px < self.peak_px:
                        continue  # player still rising at destination, cannot land
                    if not self._arc_clear(node.pos, pos, chunk):
                        continue

                g = node.g + self.manhatten_dist(node.pos, pos)
                h = self.manhatten_dist(pos, final_pos)
                child = Node(node, pos, g, h)

                if child not in open_set:
                    open_set.add(child)
                    hp.heappush(open_queue, (g + h, child))

        return [] if return_path else False



