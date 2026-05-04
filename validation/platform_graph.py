import config 
import numpy as np

class PlatformGraph():
    """Class will generate a graph from using the game physics and the map"""

    def __init__(self):
        self.v_jump = config.JUMP_SPEED
        self.g = config.GRAVITY
        self.v_x = config.MOVE_SPEED
        self.v_max = config.MAX_FALL_SPEED
        self.t_max = (self.v_jump + self.v_max) / self.g

        # Pre calculates all the possible
        self.max_y_dict = {}
        self.calc_max_y(np.arange(config.SCREEN_WIDTH))

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
    
    def _reachable(self, pos1: tuple[int, int], pos2: tuple[int, int]):
        dx = pos2[0] - pos2[0]
        if pos2[1] < self.max_y_dict[dx]  + 2*pos1[1]:
            return True
        return False

    def _is_ground(self, pos: tuple[int, int], chunk: np.ndarray) -> bool:
        x, y = pos
        if (chunk[x, y] == 0 & chunk[x, y-1] == 1):
            return True
        return False
    
    def traverse_chunk(self, start_pos, chunk):
        """Need to implement still. Will check from start position all possible nodes it can expand. It will iteratively keep expanding the nodes untill it has found exit or not able to expand further."""
        
        nodes = np.where()
