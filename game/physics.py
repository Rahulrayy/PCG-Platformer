import arcade
from config import GRAVITY, MAX_FALL_SPEED

class PhysicsEngine:
    def __init__(self, player, walls: arcade.SpriteList):
        self.player = player
        self.walls  = walls

    def update(self, dt: float):
        #gravity
        self.player.vel_y -= GRAVITY * dt
        if self.player.vel_y < -MAX_FALL_SPEED:
            self.player.vel_y = -MAX_FALL_SPEED

        # horizontal plus collison
        self.player.center_x += self.player.vel_x * dt
        for wall in arcade.check_for_collision_with_list(self.player, self.walls):
            if self.player.vel_x > 0:
                self.player.right = wall.left
            elif self.player.vel_x < 0:
                self.player.left  = wall.right
            self.player.vel_x = 0.0
            break

        # vertical plus colliosn
        self.player.on_ground = False
        self.player.center_y += self.player.vel_y * dt

        for wall in arcade.check_for_collision_with_list(self.player, self.walls):
            if self.player.vel_y <= 0:      # falling/standing
                self.player.bottom = wall.top
                self.player.on_ground = True
                self.player.vel_y = 0.0
            elif self.player.vel_y > 0:     #jumping up into a ceiling
                self.player.top  = wall.bottom
                self.player.vel_y = 0.0
            break