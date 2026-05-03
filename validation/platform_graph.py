import config 

class PlatformGraph():
    """Class will generate a graph from using the game physics and the map"""

    def __init__(self, chunk):
        self.v_jump = config.JUMP_SPEED
        self.g = config.GRAVITY
        self.v_x = config.MOVE_SPEED
        self.v_max = config.MAX_FALL_SPEED
        self.t_max = (self.v_jump + self.v_max) / self.g
        self.chunk = chunk

    def _max_y(self, dx: int) -> int:
        t1 = dx / self.v_x

        if t1 <= self.t_max:
            y_max = self.v_jump * t1 - (self.g * (t1 ** 2)) / 2 # fall is parabolic if t1 <= t_max

        else:
            y_max = self.v_jump * self.t_max - (self.g * (self.t_max ** 2)) / 2 - self.v_max * (t1 - self.t_max) # fall becomes linear after t1 > t_max
    
        return int(y_max)
    
    def _reachable(self, pos1: tuple[int, int], pos2: tuple[int, int]):
        x1, y1 = pos1
        x2, y2 = pos2

        dx = x2 - x1
        max_y = self._max_y(dx)
        if y2 - y1 < max_y:
            return True
        return False

    def _is_ground(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        if (self.chunk[x, y] == 0 & self.chunk[x, y-1] == 1):
            return True
        return False
    
    def traverse_chunk(self, start_pos):
        """Need to implement still. Will check from start position all possible nodes it can expand. It will iteratively keep expanding the nodes untill it has found exit or not able to expand further."""
        pass
