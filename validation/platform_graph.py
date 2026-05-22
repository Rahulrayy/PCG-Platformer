import config 
import numpy as np
import heapq as hp

class Node:
    def __init__(self, parent, pos, g, h):
        self.x = pos[1]
        self.y = pos[0]
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
    
    def _reachable(self, pos: tuple[int, int], ground_blocks: list[tuple[int, int]]):
        reachable_list = []                                             # List contains reachable block positions
        for block in ground_blocks:

            if block[1] <= pos[1]:                                      # Only look forward
                continue

            dx = (block[1] - pos[1])*config.TILE_SIZE                   # Convert to pixel size
            max_y = self.max_y_dict.get(dx, -float("inf"))              # If it is not in the lookup dict, ignore     
            if ((pos[0] - block[0]) * config.TILE_SIZE < max_y):        # If reachable, add to reachable list
                reachable_list.append(block)
        
        return reachable_list

    def _is_ground(self, chunk: np.ndarray):
        ground_diff = np.zeros_like(chunk)
        ground_diff[:-1, :] = chunk[1:, :] - chunk[:-1, :] # 1 where empty tile has solid tile directly below
        ground_blocks = zip(*np.where(ground_diff == 1))
        return list(ground_blocks)
    
    def _arc_clear(self, pos1: tuple[int, int], pos2: tuple[int, int], chunk: np.ndarray) -> bool:
        """Returns False if a solid tile blocks the jump arc between pos1 and pos2."""
        for col in range(pos1[1] + 1, pos2[1]):
            t = (col - pos1[1]) * config.TILE_SIZE / self.v_x
            if t <= self.t_max:
                y_offset_px = self.v_jump * t - (self.g * t ** 2) / 2
            else:
                y_offset_px = self.v_jump * self.t_max - (self.g * self.t_max ** 2) / 2 - self.v_max * (t - self.t_max)
            arc_row = pos1[0] - y_offset_px / config.TILE_SIZE  # up = decreasing row
            for row in [int(arc_row), int(arc_row) - 1]:  # check feet and head (player is 1 tile tall)
                if 0 <= row < chunk.shape[0] and chunk[row, col] == 1:
                    return False
        return True

    def manhatten_dist(self, pos1, pos2):
        return abs(pos1[1]-pos2[1]) + abs(pos1[0] - pos2[0])
    
    def column_dist(self, x, final_x):
        """Since we dont care about the height of the player when checking if the player is at the end, 
        we can just use the horizontal distance. This is guaranteed to be admissable"""
        return abs(x - final_x)

    def a_star(self, start: tuple[int, int], final: tuple[int, int], chunk: np.ndarray):

        # Initialize the open set for A-star
        start_node = Node(None, start, 0, self.column_dist(start[1], final[1]))
        open_queue = [(start_node.g + start_node.h, start_node)]
        hp.heapify(open_queue)
        open_dict = {start_node.pos: start_node.g} # Keep track of g so we know if we need to skip node or expand

        closed_set = set({}) 

        ground_blocks = self._is_ground(chunk) # Detects all the ground blocks

        while open_queue:
            score, node = hp.heappop(open_queue)
            
            # Any position at the final column (column = x), is a valid final position
            if node.pos == final:
                return True

            # Already traversed
            if (node.pos in closed_set):
                continue 
            
            # Remove from open and add to closed 
            closed_set.add(node.pos)
            
            for child in self._reachable(node.pos, ground_blocks):
            
                # Skip in if closed set
                if child in closed_set:
                    continue

                # Check if no blocks are in the way
                if child[1] < node.pos[1] and not self._arc_clear(node.pos, child, chunk):  # upward jumps only
                    continue
                
                child_g = node.g + self.column_dist(child[1], node.pos[1])

                # If child in open dict but value is higher, skip
                if child in open_dict:
                    if child_g >= open_dict.get(child, float("inf")):
                        continue
                
                # If child not in open set or value is lower, update/add child to open_dict
                open_dict[child] = child_g
                child_h = self.column_dist(child[1], final[1])
                child_node = Node(node, child, child_g, child_h)

                # We can always push the child to the heap because it has a lower 'g' value than other instance → will get popped earlier
                hp.heappush(open_queue, (child_g + child_h, child_node))

        return False
                



