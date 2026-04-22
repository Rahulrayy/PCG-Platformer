import arcade
from config import TILE_SIZE, COLOR_PLAYER, MOVE_SPEED, JUMP_SPEED

class Player(arcade.SpriteSolidColor):
    """
    The player character is slightly smaller in both dims than a tile so it can walk through 1 tile gaps

    vel_x / vel_y are in pixels per second, physics engine owns them after theyre set here.
    """

    WIDTH  = int(TILE_SIZE * 0.70)   # 33 px
    HEIGHT = int(TILE_SIZE * 0.90)   # 43 px

    def __init__(self):
        super().__init__(self.WIDTH, self.HEIGHT, COLOR_PLAYER)
        self.vel_x:    float = 0.0
        self.vel_y:    float = 0.0
        self.on_ground: bool = False   # set each frame by the physics engine

    # called on every frame

    def apply_input(self, keys_held: dict):
        """sets horizontal velocity based on A/D keys """
        if keys_held.get(arcade.key.A):
            self.vel_x = -MOVE_SPEED
        elif keys_held.get(arcade.key.D):
            self.vel_x =  MOVE_SPEED
        else:
            self.vel_x = 0.0

    # no need to cllhump on each frame so called on button press
    def try_jump(self):
        if self.on_ground:
            self.vel_y     = JUMP_SPEED
            self.on_ground = False