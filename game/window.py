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

        self.background_list: arcade.SpriteList | None = None
        self.chunk_mgr: ChunkManager    | None = None
        self.player:    Player          | None = None
        self.physics:   PhysicsEngine   | None = None
        self.camera:    Camera          | None = None
        
        self.score:     Score                  = Score()
        self.keys:      dict                   = {}
        self._fps:      float                  = 0.0

        self._show_ghost:      bool            = False
        self._ghost_sprites:   arcade.SpriteList = arcade.SpriteList()
        self._ghost_tex                         = None
        self._ghost_chunk_index: int            = -1

    def setup(self):
        self.background_list = arcade.SpriteList()
        
        bg_textures = arcade.load_spritesheet(
            "assets\\Background_n_details.png",
            sprite_width=64, 
            sprite_height=64, 
            columns=4, 
            count=8
        )
        
        bg = arcade.Sprite()
        bg.texture = bg_textures[0] 
        bg.scale = SCREEN_WIDTH / 64
        bg.center_x = SCREEN_WIDTH / 2
        bg.center_y = SCREEN_HEIGHT / 2
        self.background_list.append(bg)

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

        self._show_ghost = False
        self._ghost_sprites = arcade.SpriteList()
        self._ghost_chunk_index = -1

    def on_key_press(self, key, modifiers):
        self.keys[key] = True
        if key == arcade.key.W or key == arcade.key.SPACE:
            self.player.try_jump()
        if key == arcade.key.H:
            self._toggle_ghost()

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

        # Auto-recompute ghost when the player enters a new chunk
        if self._show_ghost and self.chunk_mgr._current_index != self._ghost_chunk_index:
            self._compute_ghost()
        
        self.player.update_animation(delta_time)

        if self.player.bottom < -100:
            self.score.save()
            self.score.reset()
            self.setup()

    def on_draw(self):
        self.clear()

        if self.background_list:
            self.background_list.draw(pixelated=True)

        self.camera.use_game()
        self.chunk_mgr.walls.draw(pixelated=True)
        self.player.draw(pixelated=True)

        if self._show_ghost and self._ghost_sprites:
            look_ahead = 20 * TILE_SIZE
            for s in self._ghost_sprites:
                if self.player.center_x - TILE_SIZE < s.center_x <= self.player.center_x + look_ahead:
                    s.draw()

        self.camera.use_gui()

        arcade.draw_text(
            f"Distance: {self.score.tiles_traveled}m",
            20, SCREEN_HEIGHT - 40,
            arcade.color.WHITE, 18, bold=True
        )

        arcade.draw_text(
            f"Best: {self.score.best_tiles}m",
            20, SCREEN_HEIGHT - 66,
            (180, 180, 60), 14, bold=True
        )

        hint = "H: Hide ghost" if self._show_ghost else "H: Show ghost"
        arcade.draw_text(
            f"W: Jump | A/D: Move | {hint}",
            20, SCREEN_HEIGHT - 90,
            (160, 160, 160), 13
        )

        arcade.draw_text(
            f"FPS: {self._fps:.0f}",
            SCREEN_WIDTH - 80, SCREEN_HEIGHT - 40,
            (120, 120, 120), 13
        )

    def _toggle_ghost(self):
        if self._show_ghost:
            self._show_ghost = False
            self._ghost_sprites = arcade.SpriteList()
        else:
            self._compute_ghost()
            self._show_ghost = True

    def _compute_ghost(self):
        from validation.headless_runner import record_headless
        from validation.platform_graph import PlatformGraph

        index = self.chunk_mgr._current_index
        entry = self.chunk_mgr._loaded.get(index)
        if not entry:
            self._ghost_sprites = arcade.SpriteList()
            return

        chunk = entry['chunk']
        chunk_offset = index * self.chunk_mgr._chunk_px_width
        rows = chunk.tiles.shape[0]

        # Lazy-load ghost texture (first idle frame, same sprite sheet as player)
        if self._ghost_tex is None:
            tex_list = arcade.load_spritesheet(
                "assets\\Char_Robot.png",
                sprite_width=48, sprite_height=48,
                columns=8, count=48
            )
            self._ghost_tex = tex_list[16]

        # Prefer headless path (most realistic); fall back to A* tile path
        positions = record_headless(chunk)  # chunk-local pixel coords
        if positions:
            world_positions = [(chunk_offset + cx, cy) for cx, cy in positions]
        else:
            _graph = PlatformGraph()
            start_pos = (0, chunk.entry_row)
            final_pos  = (chunk.width_tiles - 1, chunk.exit_row)
            path = _graph.a_star(start_pos, final_pos, chunk.tiles, return_path=True)
            # (col, row) -> world pixel center; row is the empty tile, solid is at row+1
            world_positions = [
                (chunk_offset + col * TILE_SIZE + TILE_SIZE // 2,
                 (rows - row - 1) * TILE_SIZE + 12)
                for col, row in path
            ]

        self._ghost_sprites = arcade.SpriteList()
        for wx, wy in world_positions:
            s = arcade.Sprite()
            s.texture = self._ghost_tex
            s.center_x = wx
            s.center_y = wy
            s.alpha = 90
            self._ghost_sprites.append(s)

        self._ghost_chunk_index = index