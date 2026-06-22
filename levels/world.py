import pygame as pg
import random
import constants as c
from enemy_data import ENEMY_SPAWN_DATA
from enemy import Enemy, Necromancer

class World():
    def __init__(self, data, map_image, enemy_images, clock):
        self.level = 1
        self.game_speed = 1
        self.health = c.HEALTH
        self.silver = c.SILVER
        self.level_data = data
        self.image = map_image
        self.tile_map = []
        self.waypoints = []
        self.no_tower_zones = []
        self.cliff_tower_zones = []
        self.warrior_count = 0
        self.warrior_max = 14
        self.global_tower_limit = c.GLOBAL_TOWER_LIMIT

        self.enemy_images = enemy_images
        self.enemy_group = pg.sprite.Group()
        self.tower_group = pg.sprite.Group()

        self.enemy_list = []
        self.spawned_enemies = 0
        self.killed_enemies = 0
        self.missed_enemies = 0
        self.enemy_spawn_counts = {}
        self.level_reward = 100
        self.reward_increment = 25
        self.max_reward_increment = 300
        self.max_level_reward = 7000
        self.blocked_tiles = set()
        self.victory = False
        self.clock = clock
        self.wave_active = False

        self.lightning_effects = []

    def process_data(self):
        self.waypoints = []
        self.no_tower_zones = []
        self.cliff_tower_zones = []
        for layer in self.level_data["layers"]:
            if layer["type"] == "tilelayer":
                self.tile_map = layer["data"]
            elif layer["type"] == "objectgroup":
                if layer["name"] == "waypoints":
                    for obj in layer["objects"]:
                        if "polyline" in obj:
                            ox, oy = obj["x"], obj["y"]
                            for pt in obj["polyline"]:
                                self.waypoints.append((ox + pt["x"], oy + pt["y"]))
                elif layer["name"] == "no_tower_zone":
                    for obj in layer["objects"]:
                        self.no_tower_zones.append(pg.Rect(obj['x'], obj['y'], obj['width'], obj['height']))
                elif layer["name"] == "cliff_tower_zone":
                    for obj in layer["objects"]:
                        self.cliff_tower_zones.append(pg.Rect(obj['x'], obj['y'], obj['width'], obj['height']))

    def process_enemies(self):
        if self.level > len(ENEMY_SPAWN_DATA):
            self.victory = True
            return
        wave = ENEMY_SPAWN_DATA[self.level - 1]
        self.enemy_list = []
        for etype, amt in wave.items():
            self.enemy_list += [etype] * amt
        random.shuffle(self.enemy_list)

    def spawn_enemies(self):
        self.enemy_group.empty()
        self.spawned_enemies = 0
        self.last_enemy_spawn = 0
        self.wave_active = True

    def try_spawn_next_enemy(self, current_time):

        if self.spawned_enemies >= len(self.enemy_list):
            return

        spawn_point = pg.math.Vector2(self.waypoints[0])

        if not hasattr(self, 'last_enemy_spawn'):
            self.last_enemy_spawn = 0

        cooldown = c.SPAWN_COOLDOWN / self.game_speed
        time_since_last_spawn = current_time - self.last_enemy_spawn

        if time_since_last_spawn < cooldown:
            return

        for enemy in self.enemy_group:
            dist = enemy.pos.distance_to(spawn_point)
            if dist < c.MIN_SPAWN_DISTANCE:
                return

        enemy_type = self.enemy_list[self.spawned_enemies]

        if enemy_type == "necromancer":
            enemy = Necromancer(self.waypoints, self.enemy_images)
        else:
            enemy = Enemy(enemy_type, self.waypoints, self.enemy_images)

        self.enemy_group.add(enemy)
        self.spawned_enemies += 1
        self.last_enemy_spawn = current_time

    def find_closest_waypoint_ahead(self, pos):
        best_i, best_d = 1, float('inf')
        p = pg.math.Vector2(pos)
        for i, wp in enumerate(self.waypoints[1:], start=1):
            d = (pg.math.Vector2(wp) - p).length_squared()
            if d < best_d:
                best_d, best_i = d, i
        return best_i

    def spawn_enemy(self, enemy_type, pos=None):
        if enemy_type == "necromancer":
            e = Necromancer(self.waypoints, self.enemy_images)
        else:
            e = Enemy(enemy_type, self.waypoints, self.enemy_images)
        if pos is not None:
            e.pos = pg.math.Vector2(pos)
            e.rect.center = pos
            idx = self.find_closest_waypoint_ahead(e.pos)
            e.target_waypoint = idx
            e.target = pg.math.Vector2(self.waypoints[idx])
        self.enemy_group.add(e)

    def start_wave(self):
        self.killed_enemies = 0
        self.missed_enemies = 0
        self.process_enemies()
        self.spawn_enemies()
        self.try_spawn_next_enemy(pg.time.get_ticks())

    def check_level_complete(self):
        if self.spawned_enemies < len(self.enemy_list):
            return False

        if self.wave_active and len(self.enemy_group) == 0:
            self.wave_active = False
            return True

        return False

    def update_enemies(self):
        dead_enemies_this_frame = []
        for enemy in self.enemy_group:
            if enemy.health <= 0:
                dead_enemies_this_frame.append(enemy)

        self.enemy_group.update(self)

        now = pg.time.get_ticks()
        import math
        from tower import play_sound

        for enemy in dead_enemies_this_frame:
            for tower in self.tower_group:
                if tower.tower_type == "warrior" and tower.chosen_path == "path_b" and tower.upgrade_level >= 3:
                    if not tower.is_buffed:

                        dist = math.hypot(tower.x - enemy.pos[0], tower.y - enemy.pos[1])
                        if dist <= 90:

                            if random.random() < 0.50:
                                tower.soul_runes += 1

                                if tower.soul_runes >= tower.max_soul_runes:
                                    tower.soul_runes = 0
                                    tower.is_buffed = True
                                    tower.buff_expiry = now + tower.buff_duration
                                    play_sound("soul-rip")

        for effect in self.lightning_effects[:]:
            effect.update()

            if effect.finished:
                self.lightning_effects.remove(effect)

    def draw(self, surface):
        surface.blit(self.image, (0, 0))

        for e in self.enemy_group:
            e.draw(surface)