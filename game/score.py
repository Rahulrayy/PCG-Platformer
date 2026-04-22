from config import TILE_SIZE
class Score:
    """
    Tracks the furthest right the player has ever reached measured in tiles
    """

    def __init__(self):
        self._max_x: float = 0.0

    def update(self, player_x: float):
        if player_x > self._max_x:
            self._max_x = player_x

    @property
    def tiles_traveled(self) -> int:
        return int(self._max_x / TILE_SIZE)