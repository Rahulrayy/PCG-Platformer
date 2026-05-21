import arcade
from config import TILE_SIZE, MOVE_SPEED, JUMP_SPEED, CHUNK_WIDTH_TILES

class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.texture_list = arcade.load_spritesheet(
            "assets\\Char_Robot.png",
            sprite_width=48, 
            sprite_height=48, 
            columns=8, 
            count=48
        )

        self.idle_textures = self.texture_list[16:20]
        self.run_textures  = self.texture_list[8:15]
        self.jump_textures = self.texture_list[24:29]

        self.texture = self.idle_textures[0]
        self.cur_frame = 0
        self.anim_timer = 0.0
        self.face_left = False 
        
        self.vel_x: float = 0.0
        self.vel_y: float = 0.0
        self.on_ground: bool = False
        
        self.hit_box = [
            (-10, -12), 
            ( 10, -12), 
            ( 10,  12), 
            (-10,  12)
        ]

    def apply_input(self, keys_held: dict):
        if keys_held.get(arcade.key.A):
            self.vel_x = -MOVE_SPEED
            self.face_left = True
        elif keys_held.get(arcade.key.D):
            self.vel_x = MOVE_SPEED
            self.face_left = False
        elif keys_held.get(arcade.key.L):
            # skip opening segment
            self.center_x = TILE_SIZE * CHUNK_WIDTH_TILES - TILE_SIZE * 5
        else:
            self.vel_x = 0.0

    def try_jump(self):
        if self.on_ground:
            self.vel_y = JUMP_SPEED
            self.on_ground = False

    def update_animation(self, delta_time: float = 1/60):
        if not self.on_ground:
            new_frames = self.jump_textures
        elif self.vel_x != 0:
            new_frames = self.run_textures
        else:
            new_frames = self.idle_textures

        if hasattr(self, 'current_frames') and self.current_frames != new_frames:
            self.cur_frame = 0
        
        self.current_frames = new_frames

        self.anim_timer += delta_time
        if self.anim_timer > 0.08:
            self.cur_frame = (self.cur_frame + 1) % len(self.current_frames)
            self.texture = self.current_frames[self.cur_frame]
            self.anim_timer = 0

        if self.face_left:
            if self.width > 0: self.width *= -1
        else:
            self.width = abs(self.width)