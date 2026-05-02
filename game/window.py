import arcade

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE,
    TILE_SIZE, COLOR_BACKGROUND, CHUNK_HEIGHT_TILES,
)
from level.opening_segment import make_opening_segment
from level.tilemap import chunk_to_sprite_list
from game.player import Player
from game.physics import PhysicsEngine
from game.camera import Camera
from game.chunk_manager import ChunkManager
from game.score import Score

class GameWindow(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(COLOR_BACKGROUND)

        self.chunk_mgr: ChunkManager    | None = None
        self.player:    Player          | None = None
        self.physics:   PhysicsEngine   | None = None
        self.camera:    Camera          | None = None
        self.score:     Score                  = Score()
        self.keys:      dict            = {}
        self._fps:      float           = 0.0

    def setup(self):
        opening       = make_opening_segment()
        opening_walls = chunk_to_sprite_list(opening)
        self.chunk_mgr = ChunkManager(opening, opening_walls)

        self.player = Player()
        spawn_platform_top = (CHUNK_HEIGHT_TILES - 1 - 9) * TILE_SIZE + TILE_SIZE
        self.player.center_x = TILE_SIZE * 6
        self.player.bottom   = spawn_platform_top + 2

        self.physics = PhysicsEngine(self.player, self.chunk_mgr.walls)
        self.camera  = Camera()
        self.camera.update(self.player, self.chunk_mgr.world_pixel_width)

    def on_key_press(self, key, modifiers):
        self.keys[key] = True
        if key == arcade.key.W:
            self.player.try_jump()

    def on_key_release(self, key, modifiers):
        self.keys[key] = False

    def on_update(self, delta_time: float):
        if delta_time > 0:
            raw_fps = 1.0 / delta_time
            self._fps = self._fps * 0.9 + raw_fps * 0.1

        self.player.apply_input(self.keys)
        self.physics.update(delta_time)
        self.chunk_mgr.update(self.player.center_x)
        self.camera.update(self.player, self.chunk_mgr.world_pixel_width)
        self.score.update(self.player.center_x)

        if self.player.bottom < 0:
            self.setup()

    def on_draw(self):
        self.clear()

        self.camera.use_game()
        self.chunk_mgr.walls.draw()
        self.player.draw()

        self.camera.use_gui()

        arcade.draw_text(
            f"Distance- {self.score.tiles_traveled} meters",  # actually tiles but mts looked better inside game
            start_x=20, start_y=SCREEN_HEIGHT - 40,
            color=arcade.color.WHITE,
            font_size=18,
            bold=True,
        )

        arcade.draw_text(
            "W: jump    A/D- move",
            start_x=20, start_y=SCREEN_HEIGHT - 68,
            color=(160, 160, 160),
            font_size=13,
        )

        arcade.draw_text(
            f"FPS: {self._fps:.0f}",
            start_x=SCREEN_WIDTH - 100, start_y=SCREEN_HEIGHT - 40,
            color=(120, 120, 120),
            font_size=13,
        )