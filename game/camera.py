import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class Camera:
    """
    Wraps two arcade.Camera instances     game_cam-  follows the player, clamped to chunk bounds.
      gui_cam- stays fixed at the origin so HUD text doesn't scroll.
    """
    def __init__(self):
        self.game_cam = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_cam  = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self._x = 0.0   # current camera left edge in world coords

    def update(self, player, world_pixel_width: int):
        #target the camera so the player is horizontally centred
        target_x = player.center_x - SCREEN_WIDTH / 2

        #never show outside the chunk on either side.
        max_x = world_pixel_width - SCREEN_WIDTH
        target_x = max(0.0, min(target_x, float(max_x)))

        self._x = target_x
        # speed=1.0 -instant follow .
        self.game_cam.move_to((target_x, 0.0), speed=1.0)

    def use_game(self):
        #camera before anything else
        self.game_cam.use()

    def use_gui(self):
        self.gui_cam.use()

    @property
    def x(self) -> float:
        return self._x