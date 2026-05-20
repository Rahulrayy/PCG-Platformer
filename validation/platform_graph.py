import config 
import numpy as np
import heapq as hp

class Node:
    def __init__(self, parent, pos, g):
        self.x = pos[0]
        self.y = pos[1]
        self.pos = pos
        self.parent = parent
        self.g = g
        self._h = None
        self._f = None

    def __eq__(self, other):
        assert isinstance(other, Node), "Can only compare nodes with each other"
        if other.x == self.x and other.y == self.y:
            return True
        return False
    
    def __hash__(self):
        return hash((self.x, self.y))

    def get_f(self):
        return self._f
    
    def f(self) -> int:
        self._f = self.h + self.g
        return self._f
    

    def get_h(self):
        return self._h
    
    def h(self, final_pos: tuple[int, int]) -> int:
        self._h = self.manhatten(self.pos, final_pos)
        return self._h
    
    
    def manhatten(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        return np.sum(np.abs(np.array(pos1) - np.array(pos2)))


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

        # yₘₐₓ = v⋅t - g⋅t² / 2  
        if t1 <= self.t_max:
            y_max = self.v_jump * t1 - (self.g * (t1 ** 2)) / 2 # fall is parabolic if t ≤ tₘₐₓ 

        else:
            y_max = self.v_jump * self.t_max - (self.g * (self.t_max ** 2)) / 2 - self.v_max * (t1 - self.t_max) # fall becomes linear after t > tₘₐₓ 
    
        return int(y_max)
    
    def _reachable(self, pos1: tuple[int, int], grid_shape: tuple[int, int]):
        y_coords, x_coords = np.indices(grid_shape)
        dx = x_coords - pos1[0] 

        max_y_lookup = np.array([self.max_y_dict.get(d, 0) for d in range(np.min(dx), np.max(dx) + 1)])
        lookup_indices = dx - np.min(dx)
        max_y_values = max_y_lookup[lookup_indices]
        reachable_mask = (y_coords < (max_y_values + 2 * pos1[1]))
        return reachable_mask

    def _is_ground(self,chunk: np.ndarray):
        ground_chunk = chunk[:, :-1] - chunk[:, 1:]
        copy_chunk = np.zeros_like(chunk)
        copy_chunk[:, 1:] = ground_chunk
        ground_mask = (copy_chunk == 1)
        return ground_mask
    
    def manhatten_dist(self, pos1, pos2):
        return np.sum(np.abs(np.array(pos1) - np.array(pos2)))
    
    def g(self, parent: Node , child: Node | tuple[int, int]) -> int:

        if isinstance(child, Node):
            child_pos = child.pos
        else: child_pos = child
        g = self.manhatten_dist(parent.pos, child_pos) + parent.g
        return g
    


    def a_star(self, start_pos, final_pos, chunk):
        """Need to implement still. Will check from start position all possible nodes it can expand. It will iteratively keep expanding the nodes untill it has found exit or not able to expand further."""
        
        start_node = Node(None, start_pos, 0)
        
        open_queue = [(0,start_node)] # (f_score, node) pairs
        open_queue = hp.heapify(open_queue)
        open_set = set([start_node])

        closed_set = set({})

        while open_set:
            score, node = hp.heappop(open_queue)
            child_mask = (self._is_ground(chunk) & self._reachable(node.pos, self.screen_shape))
            childs_pos = zip(*np.where(child_mask)) # Creates tuples of (r, c) for all the child nodes
            for r, c in childs_pos:
                if (r,c) == final_pos:
                    break
                child_g = self.g(parent=node, child=(r, c))
                child = Node(parent=node.pos, pos=(r,c), g=child_g)
                h = child.h(final_pos=final_pos)
                f = child.f()
            