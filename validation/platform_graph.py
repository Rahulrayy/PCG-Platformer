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
        self.t_max = (self.v_jump + self.v_max) / self.g

        self.screen_width = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT
        self.screen_shape = (config.SCREEN_HEIGHT, config.SCREEN_WIDTH)

        # Pre calculates all the possible
        self.max_y_dict = {}
        self.calc_max_y(np.arange(self.screen_width))

    def calc_max_y(self, arr_x):
        for xi in arr_x:
            max_y = self._max_y(dx=xi)
            self.max_y_dict[xi] = max_y

    def _max_y(self, dx: int) -> int:
        """Possibly pre compute all the possible dx, dy combinations to save computational cost"""
        t1 = dx / self.v_x

        if t1 <= self.t_max:
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
        max_y_lookup = np.array([self.max_y_dict.get(d, 0) for d in range(min_px, max_px + 1)])
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

    def a_star(self, start_pos, final_pos, chunk):
        """Will check from start position all possible nodes it can expand......it will iteratively keep expanding the nodes untill it has found exit or not able to expand further."""

        start_node = Node(None, start_pos, 0, self.manhatten_dist(start_pos, final_pos))

        open_queue = [(start_node.g + start_node.h, start_node)]
        hp.heapify(open_queue)
        open_set = {start_node}

        closed_set = set()

        ground_rows, ground_cols = self._is_ground(chunk)
        child_positions = [(int(c), int(r)) for r, c in zip(ground_rows, ground_cols)]

        while open_queue:
            score, node = hp.heappop(open_queue)

            if node.pos in closed_set:
                open_set.discard(node)  # remove stale duplicate so open_set stays accurate
                continue

            if node.x == final_pos[0]:  # any ground tile on the right edge column is a valid exit
                return True

            open_set.discard(node)
            closed_set.add(node.pos)

            reachable_mask = self._reachable(node.pos, chunk.shape)

            for pos in child_positions:
                if pos in closed_set:
                    continue
                if not reachable_mask[pos[1], pos[0]]:
                    continue
                if pos[1] < node.pos[1] and not self._arc_clear(node.pos, pos, chunk):  # upward jumps only
                    continue

                g = node.g + self.manhatten_dist(node.pos, pos)
                h = self.manhatten_dist(pos, final_pos)
                child = Node(node, pos, g, h)

                if child not in open_set:
                    open_set.add(child)
                    hp.heappush(open_queue, (g + h, child))

        return False



