import pygame as pg
import pygame.gfxdraw
from pygame.math import Vector2
import math
import random
import constants as c
from enemy_data import ENEMY_DATA
from sound_cache import SOUND_CACHE
import time

BLOOD_RED = (200, 0, 0)

def draw_furantur(surface, tower_pos, necro_pos):
    time_now = pg.time.get_ticks()

    dx = necro_pos[0] - tower_pos[0]
    dy = necro_pos[1] - tower_pos[1]

    distance = math.hypot(dx, dy)
    if distance == 0:
        return

    nx = dx / distance
    ny = dy / distance

    px = -ny
    py = nx

    beam_width = 6


    top_start = (tower_pos[0] + px * beam_width / 2, tower_pos[1] + py * beam_width / 2)
    top_end = (necro_pos[0] + px * beam_width / 2, necro_pos[1] + py * beam_width / 2)
    bottom_start = (tower_pos[0] - px * beam_width / 2, tower_pos[1] - py * beam_width / 2)
    bottom_end = (necro_pos[0] - px * beam_width / 2, necro_pos[1] - py * beam_width / 2)
    pg.gfxdraw.filled_polygon(surface, [top_start, top_end, bottom_end, bottom_start], BLOOD_RED)
    pg.gfxdraw.aapolygon(surface, [top_start, top_end, bottom_end, bottom_start], BLOOD_RED)

    speed = 0.0015
    progress = (time_now * speed) % 1
    pulse_length = 110
    start_d = progress * distance
    end_d = min(start_d + pulse_length, distance)
    step = 6

    for d in range(int(start_d), int(end_d), step):
        x = tower_pos[0] + nx * d
        y = tower_pos[1] + ny * d

        t = (d - start_d) / pulse_length
        radius = 2.8 + math.sin(t * math.pi) * 3

        shift = 0
        fx = x + px * shift
        fy = y + py * shift

        pg.gfxdraw.filled_circle(surface, int(fx), int(fy), int(radius), BLOOD_RED)
        pg.gfxdraw.aacircle(surface, int(fx), int(fy), int(radius), BLOOD_RED)

ANIMATION_FRAMES = [
    pg.Rect(0, 0, 81, 48),
    pg.Rect(80, 0, 67, 48),
    pg.Rect(146, 0, 64, 48),
    pg.Rect(209, 0, 91, 48),
    pg.Rect(295, 0, 85, 48),
    pg.Rect(0, 0, 81, 48),
]

def extract_frames(sprite_sheet):
    return [sprite_sheet.subsurface(rect).copy() for rect in ANIMATION_FRAMES]

class Enemy(pg.sprite.Sprite):
    def __init__(self, enemy_type, waypoints, images):
        super().__init__()
        self.enemy_type = enemy_type
        self.waypoints = waypoints
        self.pos = Vector2(self.waypoints[0])
        self.target_waypoint = 1
        self.target = Vector2(self.waypoints[self.target_waypoint])
        enemy_stats = ENEMY_DATA.get(enemy_type)
        self.max_health = enemy_stats["health"]
        self.health = self.max_health
        self.speed = enemy_stats["speed"]
        self.reward = enemy_stats.get("reward", 10)
        self.angle = 0
        self.incoming_damage = 0
        self.stunned = False
        self.stun_end_time = 0
        self.last_dragon_stun_time = 0
        self.frames = None
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_delay = 120
        if enemy_type in images:
            loaded = images[enemy_type]
            self.frames = loaded if isinstance(loaded, list) else [loaded]
        else:
            raise ValueError(f"Missing enemy image for: {enemy_type}")
        self.original_image = self.frames[0]
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.pos)


    def update(self, world):
        self.animate(world)
        self.move(world)
        self.rotate()
        self.check_alive(world)

    def animate(self, world):
        if self.frames and len(self.frames) > 1:
            self.animation_timer += world.clock.get_time()
            if self.animation_timer >= self.frame_delay:
                self.animation_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.original_image = self.frames[self.frame_index]
        else:
            self.original_image = self.frames[0]

    def move(self, world):
        current_time = pg.time.get_ticks()

        if self.stunned:
            if current_time >= self.stun_end_time:
                self.stunned = False
            else:
                return
        if self.target_waypoint >= len(self.waypoints):
            if world.health > 1:
                SOUND_CACHE["hit_sound"].set_volume(0.1)
                SOUND_CACHE["hit_sound"].play()
            else:
                SOUND_CACHE["death_sound"].play()
            self.kill()
            world.health -= 1
            world.missed_enemies += 1
            return
        direction = self.target - self.pos
        distance = direction.length()
        if distance != 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * world.game_speed
        next_target = Vector2(self.waypoints[self.target_waypoint])
        prev_target = Vector2(self.waypoints[self.target_waypoint - 1]) if self.target_waypoint > 0 else self.pos
        to_current = next_target - prev_target
        to_enemy = self.pos - prev_target
        if to_enemy.dot(to_current) >= to_current.length_squared():
            self.target_waypoint += 1
            if self.target_waypoint < len(self.waypoints):
                self.target = Vector2(self.waypoints[self.target_waypoint])

    def rotate(self):
        dist = self.target - self.pos
        self.angle = math.degrees(math.atan2(-dist[1], dist[0]))
        self.image = pg.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

    def check_alive(self, world):
        if self.health <= 0:
            world.killed_enemies += 1
            world.silver += self.reward
            self.kill()

    def take_damage(self, amount):
        self.health -= amount
        self.incoming_damage -= amount
        if self.health <= 0:
            self.kill()

    def get_predicted_pos(self, delay_ms):
        if self.target_waypoint >= len(self.waypoints):
            return self.pos

        direction = self.target - self.pos
        distance = direction.length()

        if distance == 0:
            return self.pos

        direction = direction.normalize()

        speed_per_ms = self.speed * 0.001 * 16

        predicted_move = direction * speed_per_ms * delay_ms

        return self.pos + predicted_move

    def draw(self, surface):
        if self.rect.collidepoint(pg.mouse.get_pos()):
            bar_width = 50
            bar_height = 6
            offset_y = 40

            x = self.pos.x - bar_width // 2
            y = self.pos.y - offset_y

            pg.draw.rect(surface, (120, 0, 0), (x, y, bar_width, bar_height))

            ratio = max(0, self.health / self.max_health)
            pg.draw.rect(surface, (0, 200, 0), (x, y, int(bar_width * ratio), bar_height))

        surface.blit(self.image, self.rect.topleft)

        if hasattr(self, "is_casting_hook") and self.is_casting_hook:
            for tower in self.hooked_towers:
                draw_furantur(surface, tower.rect.center, self.rect.center)



class Necromancer(Enemy):
    def __init__(self, waypoints, images):
        walk_frames = images["necromancer_walk"]
        summon_frames = images["necromancer_summon"]

        super().__init__("necromancer", waypoints, {"necromancer": walk_frames})

        self.summon_frames = summon_frames
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_delay = c.ANIMATION_DELAY
        self.summoning = False
        self.spawn_timer = 0
        self.spawn_cooldown = 4000


        self.is_casting_hook = False
        self.hook_duration = 5000
        self.hook_cooldown = 5000
        self.last_hook_time = 0
        self.furantur_start_time = 0
        self.hooked_towers = []
        self.furantur_radius = 250
        self.furantur_timer = 0
        self.furantur_sound = SOUND_CACHE["furantur"]
        self.furantur_channel = pg.mixer.Channel(5)
        self.furantur_casting = False
        self.furantur_cast_start = 0
        self.furantur_cast_time = 2600
        self.furantur_cast_sound = SOUND_CACHE["furantur_cast_sound"]

    def update(self, world):

        dt = world.clock.get_time() * world.game_speed

        self.spawn_timer += dt

        if self.spawn_timer >= self.spawn_cooldown:
            self.spawn_timer -= self.spawn_cooldown
            self.summoning = True
            SOUND_CACHE["necro_spawn"].play()

            spawn_pos = (self.pos.x + 5, self.pos.y)
            world.spawn_enemy("shrieker", spawn_pos)

        self.furantur_timer += dt
        current_time = pg.time.get_ticks()

        if (not self.is_casting_hook
                and not self.furantur_casting
                and self.furantur_timer >= self.hook_cooldown):
            self.furantur_casting = True
            self.furantur_cast_start = current_time
            self.furantur_cast_sound.play()

        if self.furantur_casting:
            if current_time - self.furantur_cast_start >= self.furantur_cast_time:
                self.furantur_casting = False
                self.start_furantur(world)

        if self.is_casting_hook and self.furantur_timer >= self.hook_duration:
            self.end_hook()

        self.animate(world)

        if not self.summoning:
            self.move(world)
            self.rotate()
            self.check_alive(world)

    def animate(self, world):
        current_frames = self.summon_frames if self.summoning else self.frames

        self.animation_timer += world.clock.get_time()
        if self.animation_timer >= self.frame_delay:
            self.animation_timer = 0
            self.frame_index += 1

            if self.summoning:
                if self.frame_index >= len(self.summon_frames):
                    self.summoning = False
                    self.frame_index = 0
            else:
                self.frame_index %= len(self.frames)

        current_image = current_frames[self.frame_index % len(current_frames)]
        self.original_image = current_image
        self.rect = self.image.get_rect(center=self.pos)

    def start_furantur(self, world):
        self.is_casting_hook = True
        self.furantur_timer = 0

        towers = list(world.tower_group)

        if len(towers) > 0:
            amount = random.randint(1, min(30, len(towers)))
            self.hooked_towers = random.sample(towers, amount)

            for tower in self.hooked_towers:
                if hasattr(tower, "apply_necro_debuff"):
                    tower.apply_necro_debuff()

        self.furantur_channel.set_volume(0.6)
        self.furantur_channel.play(self.furantur_sound, loops=-1)
    def end_hook(self):

        self.is_casting_hook = False
        self.furantur_timer = 0

        for tower in self.hooked_towers:
            if hasattr(tower, "remove_necro_debuff"):
                tower.remove_necro_debuff()

        self.hooked_towers.clear()
        self.furantur_channel.stop()

    def get_predicted_pos(self, delay_ms):
        if self.target_waypoint >= len(self.waypoints):
            return self.pos

        direction = self.target - self.pos
        distance = direction.length()

        if distance == 0:
            return self.pos

        direction = direction.normalize()

        speed_per_ms = self.speed * 0.001 * 16

        predicted_move = direction * speed_per_ms * delay_ms

        return self.pos + predicted_move

