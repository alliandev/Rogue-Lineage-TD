import pygame as pg
import math
import constants as c
from monk_data import MONK_DATA
from warrior_data import WARRIOR_DATA
from druid_data import DRUID_DATA
from cadence_data import CADENCE_DATA
from thief_data import THIEF_DATA
import sound_cache
from lightning_effect import LightningEffect

_cadence_sound_channel = None

def set_mute_music(value: bool):
    sound_cache.mute_music = value
    pg.mixer.music.set_volume(0.0 if value else 0.5)
    if _cadence_sound_channel is not None:
        _cadence_sound_channel.set_volume(0.0 if value else 0.3)

def set_mute_sfx(value: bool):
    sound_cache.mute_sfx = value


def play_sound(sound_key):
    if sound_cache.mute_sfx:
        return None
    sound = sound_cache.SOUND_CACHE.get(sound_key)
    if sound:
        return sound.play()
    return None


class Tower(pg.sprite.Sprite):
    def __init__(self, sprite_sheets, tile_x, tile_y, tower_type="warrior"):
        global _cadence_sound_channel

        super().__init__()

        self.tower_type = tower_type
        self.upgrade_level = 1
        self.chosen_path = None
        self.cooldown_buff = 1.0
        self.chain_hits = []
        self.chain_start_time = 0
        self.chain_index = 0
        self.attacking = False
        self.last_shot = pg.time.get_ticks()
        self.damage_dealt = 0
        self.lightning_combo = 0
        self.last_lightning_hit_time = 0
        self.soul_runes = 0
        self.max_soul_runes = 5
        self.is_buffed = False
        self.buff_expiry = 0
        self.buff_duration = 10000

        if tower_type == "warrior":
            self.data = WARRIOR_DATA
            self.attack_sound_key = "warrior_attack"
        elif tower_type == "druid":
            self.data = DRUID_DATA
            self.attack_sound_key = "druid_attack_1"
        elif tower_type == "cadence":
            self.data = CADENCE_DATA
            self.attack_sound_key = "cadence_song_1"

            from sound_cache import register_cadence_channel

            if _cadence_sound_channel:
                _cadence_sound_channel.stop()
                _cadence_sound_channel = None

            if not sound_cache.mute_music and self.attack_sound_key in sound_cache.SOUND_CACHE:
                _cadence_sound_channel = sound_cache.SOUND_CACHE[self.attack_sound_key].play(loops=-1)
                if _cadence_sound_channel:
                    _cadence_sound_channel.set_volume(0.3)
                    register_cadence_channel(_cadence_sound_channel)
        elif tower_type == "thief":
            self.data = THIEF_DATA
            self.attack_sound_key = "thief_attack_1"
        elif tower_type == "monk":
            self.data = MONK_DATA
            self.attack_sound_key = "monk_attack_1"
        else:
            raise ValueError(f"Unknown tower type: {tower_type}")

        if tower_type != "cadence":
            sound = sound_cache.SOUND_CACHE.get(self.attack_sound_key)
            if sound:
                sound.set_volume(0.6)

        if tower_type == "cadence":
            level_data = self.data[self.upgrade_level - 1]
        else:
            level_data = self.data["base"]
        self.range = level_data.get("range", 0)
        self.cooldown = level_data.get("cooldown", 0)
        self.damage = level_data.get("damage", 0)
        if tower_type == "cadence":
            self.speed_buff = level_data.get("speed_buff", 1.0)
            self.song_path = level_data.get("song_path", "")

        self.tile_x = tile_x
        self.tile_y = tile_y
        self.x = self.tile_x * c.TILE_SIZE + c.TILE_SIZE // 2
        self.y = self.tile_y * c.TILE_SIZE + c.TILE_SIZE // 2

        self.sprite_sheets = sprite_sheets

        if tower_type in ("warrior", "druid", "thief", "monk"):
            if self.tower_type == "warrior":
                sheet = self.sprite_sheets["base"][self.upgrade_level - 1]
            else:
                sheet = self.sprite_sheets[self.upgrade_level - 1]

            self.animation_list = self.load_images(sheet)
            self.original_image = self.animation_list[0]
            self.image = pg.transform.rotate(self.original_image, 90)
        else:
            self.original_image = self.sprite_sheets[self.upgrade_level - 1]
            self.animation_list = [self.original_image]
            self.image = self.original_image

        self.frame_index = 0
        self.update_time = pg.time.get_ticks()
        self.angle = 90

        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        self.font = pg.font.SysFont(None, 20)

        self.range_image = pg.Surface((self.range * 2, self.range * 2), pg.SRCALPHA)
        self.range_image.fill((0, 0, 0, 0))
        pg.draw.circle(self.range_image, (255, 255, 255, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center

        if tower_type == "warrior":
            self.total_spent = c.WARRIOR_COST
        elif tower_type == "druid":
            self.total_spent = c.DRUID_COST
        elif tower_type == "cadence":
            self.total_spent = c.CADENCE_COST
        elif tower_type == "thief":
            self.total_spent = c.THIEF_COST
        elif tower_type == "monk":
            self.total_spent = c.MONK_COST
        else:
            self.total_spent = 0

    def load_images(self, sprite_sheet):
        frame_rects = [
            pg.Rect(0, 0, 81, 48),
            pg.Rect(80, 0, 67, 48),
            pg.Rect(146, 0, 64, 48),
            pg.Rect(209, 0, 91, 48),
            pg.Rect(295, 0, 85, 48),
            pg.Rect(0, 0, 81, 48),
        ]
        return [sprite_sheet.subsurface(rect).copy() for rect in frame_rects]

    def update(self, enemy_group, world):
        self.world = world

        if self.is_buffed and pg.time.get_ticks() > self.buff_expiry:
            self.is_buffed = False

        if self.tower_type == "cadence":
            return
        if self.attacking:
            if self.tower_type == "thief" and self.upgrade_level == 4 and self.chosen_path == "path_a":
                self.play_animation(world, enemy_group)
            else:
                self.update_animation(world)
        else:
            now = pg.time.get_ticks()
            if now - self.last_shot > (self.effective_cooldown / world.game_speed):
                self.pick_target(enemy_group)

    def pick_target(self, enemy_group):
        for enemy in enemy_group:
            if enemy.health > 0:
                x_dist = enemy.pos[0] - self.x
                y_dist = enemy.pos[1] - self.y
                dist = math.hypot(x_dist, y_dist)

                if dist < self.range:
                    effective_health = enemy.health - enemy.incoming_damage
                    if effective_health <= 0:
                        continue

                    self.target = enemy
                    self.angle = math.degrees(math.atan2(-y_dist, x_dist))
                    self.angle %= 360

                    if self.tower_type == "thief" and self.upgrade_level == 4 and self.chosen_path == "path_a":
                        self.prepare_chain_attack(enemy)
                    else:
                        enemy.incoming_damage += self.damage
                        self.attacking = True
                        self.frame_index = 0
                        self.update_time = pg.time.get_ticks()
                    break

    def play_animation(self, world, enemy_group):
        now = pg.time.get_ticks()
        animation_delay = c.ANIMATION_DELAY / world.game_speed

        if self.tower_type == "thief" and self.upgrade_level == 4 and self.chain_hits:
            if self.frame_index < len(self.animation_list):
                if now - self.update_time > animation_delay:
                    self.update_time = now
                    self.frame_index += 1

                    if self.frame_index == 1 and self.target and self.target.health > 0:
                        play_sound("thief_attack_2")

                self.original_image = self.animation_list[
                    min(self.frame_index, len(self.animation_list) - 1)
                ]

                self.image = pg.transform.rotate(
                    self.original_image,
                    self.angle
                )
                return

            if self.chain_index < 8:
                if now - self.chain_start_time >= self.chain_index * 400:
                    if self.chain_index >= len(self.chain_hits):
                        last_enemy = self.chain_hits[-1]

                        candidates = [
                            e for e in enemy_group
                            if e not in self.chain_hits and e.health > 0
                        ]

                        if candidates:
                            def dist_to_last(e):
                                return math.hypot(e.pos[0] - last_enemy.pos[0], e.pos[1] - last_enemy.pos[1])
                            next_enemy = min(candidates, key=dist_to_last)
                            next_enemy.incoming_damage += self.damage
                            self.chain_hits.append(next_enemy)
                        else:
                            self.chain_hits = []
                            self.chain_index = 0
                            self.attacking = False
                            self.target = None
                            self.last_shot = now
                            return

                    enemy = self.chain_hits[self.chain_index]

                    if enemy.health > 0:
                        enemy.health -= self.damage
                        enemy.incoming_damage = max(enemy.incoming_damage - self.damage, 0)
                        self.damage_dealt += self.damage

                        if self.chain_index == 0:
                            play_sound("thief_attack_2")
                        else:
                            play_sound("chain_lethality")

                    self.chain_index += 1

            else:
                self.chain_hits = []
                self.chain_index = 0
                self.attacking = False
                self.target = None
                self.last_shot = now

            return

        if now - self.update_time > animation_delay:
            self.update_time = now
            self.frame_index += 1
            if self.frame_index == 1:
                if self.target and self.target.health > 0:
                    play_sound(self.attack_sound_key)
                    if self.tower_type == "druid" and self.upgrade_level == 4:
                        lightning = LightningEffect(self.rect.center, self.target)
                        self.world.lightning_effects.append(lightning)
                else:
                    self.attacking = False
                    self.target = None
                    self.frame_index = 0
                    return
            if self.frame_index < len(self.animation_list):
                self.original_image = self.animation_list[self.frame_index]
            else:
                if self.target and self.target.health > 0:
                    self.target.health -= self.damage
                    self.target.incoming_damage = max(self.target.incoming_damage - self.damage, 0)
                    self.damage_dealt += self.damage
                self.last_shot = now
                self.attacking = False
                self.target = None
                self.frame_index = 0
                return
            self.image = pg.transform.rotate(self.original_image, self.angle)

            if self.target and self.target.health > 0:
                self.target.health -= self.damage
                self.target.incoming_damage = max(self.target.incoming_damage - self.damage, 0)
                self.damage_dealt += self.damage
                self.last_shot = now
                self.attacking = False
                self.target = None
                self.frame_index = 0

            else:
                self.original_image = self.animation_list[self.frame_index]
                self.image = pg.transform.rotate(self.original_image, self.angle)

    def update_animation(self, world):
        now = pg.time.get_ticks()
        animation_delay = c.ANIMATION_DELAY / world.game_speed

        if now - self.update_time < animation_delay:
            return

        self.update_time = now
        self.frame_index += 1

        if self.frame_index == 1:
            if self.target and self.target.health > 0:
                play_sound(self.attack_sound_key)

        if self.frame_index == 3:
            if self.target and self.target.health > 0:
                if self.tower_type == "druid" and self.upgrade_level == 4:
                    frames_remaining = len(self.animation_list) - 3
                    travel_time = int(frames_remaining * (c.ANIMATION_DELAY / world.game_speed))
                    lightning = LightningEffect(self.rect.center, self.target, travel_time)
                    self.world.lightning_effects.append(lightning)

        if self.frame_index >= len(self.animation_list):
            self.finish_attack()
            return

        self.original_image = self.animation_list[self.frame_index]

        self.original_image = self.animation_list[self.frame_index]

    def finish_attack(self):
        if self.target and self.target.health > 0:
            self.target.health -= self.damage
            self.target.incoming_damage = max(self.target.incoming_damage - self.damage, 0)
            self.damage_dealt += self.damage

            if self.tower_type == "monk":
                self.apply_monk_stun(self.target)

        self.last_shot = pg.time.get_ticks()
        self.attacking = False
        self.target = None
        self.frame_index = 0

    def get_max_level(self):
        if self.tower_type == "cadence":
            return len(self.data)
        return 4

    def needs_path_choice(self):
        if self.tower_type == "cadence":
            return False
        return self.chosen_path is None

    def choose_path(self, path: str):
        if path not in ("path_a", "path_b"):
            return
        if self.chosen_path is not None:
            return
        self.chosen_path = path

    def upgrade(self):
        if self.tower_type == "cadence":
            self._upgrade_cadence()
            return

        if self.upgrade_level >= self.get_max_level():
            print("Tower already at max level")
            return

        if self.upgrade_level == 1 and self.chosen_path is None:
            print("Choose an upgrade path first")
            return

        self._apply_upgrade()

    def _apply_upgrade(self):
        if self.upgrade_level >= self.get_max_level():
            print("Tower already at max level")
            return

        self.upgrade_level += 1
        path_list = self.data[self.chosen_path]
        path_index = self.upgrade_level - 2
        level_data = path_list[path_index]

        self.range = level_data.get("range", self.range)
        self.cooldown = level_data.get("cooldown", 0)
        self.damage = level_data.get("damage", 0)

        if self.tower_type == "druid" and self.upgrade_level == 4 and self.chosen_path == "path_a":
            self.attack_sound_key = "druid_attack_2"
            sound_cache.SOUND_CACHE[self.attack_sound_key].set_volume(0.4)

        if self.tower_type == "thief" and self.upgrade_level == 4:
            if self.chosen_path == "path_a":
                self.attack_sound_key = "thief_attack_2"
            else:
                self.attack_sound_key = "thief_attack_1"

        if self.tower_type == "monk" and self.upgrade_level == 2:
            self.attack_sound_key = "monk_attack_2"

        if self.tower_type == "monk" and self.upgrade_level == 3:
            if self.chosen_path == "path_b":
                self.attack_sound_key = "spin-kick"
            else:
                self.attack_sound_key = "monk_attack_3"

        if self.tower_type == "monk" and self.upgrade_level == 4:
            if self.chosen_path == "path_b":
                self.attack_sound_key = "spin-kick"
            else:
                self.attack_sound_key = "monk_attack_4"

        if self.tower_type == "warrior":
            if self.chosen_path == "path_b":
                sprite_index = min(self.upgrade_level - 2, len(self.sprite_sheets["path_b"]) - 1)
                sheet_to_load = self.sprite_sheets["path_b"][sprite_index]
            else:
                sprite_index = min(self.upgrade_level - 1, len(self.sprite_sheets["path_a"]) - 1)
                sheet_to_load = self.sprite_sheets["path_a"][sprite_index]
        else:
            sprite_index = min(self.upgrade_level - 1, len(self.sprite_sheets) - 1)
            sheet_to_load = self.sprite_sheets[sprite_index]

        if self.tower_type in ("warrior", "druid", "thief", "monk"):
            self.animation_list = self.load_images(sheet_to_load)
            self.original_image = self.animation_list[0]
        else:
            self.original_image = self.sprite_sheets[sprite_index]
            self.animation_list = [self.original_image]
            self.image = self.original_image

        self.frame_index = 0

        if self.tower_type == "warrior":
            cost = c.get_warrior_upgrade_cost(c.UPGRADE_WARRIOR_BASE_COST, self.upgrade_level - 1)
        elif self.tower_type == "druid":
            cost = int(c.UPGRADE_DRUID_BASE_COST * (c.UPGRADE_GROWTH_FACTOR_DRUID ** (self.upgrade_level - 2)))
        elif self.tower_type == "thief":
            cost = int(c.UPGRADE_THIEF_BASE_COST * (c.UPGRADE_GROWTH_FACTOR_THIEF ** (self.upgrade_level - 2)))
        elif self.tower_type == "monk":
            cost = int(c.UPGRADE_MONK_BASE_COST * (c.UPGRADE_GROWTH_FACTOR_MONK ** (self.upgrade_level - 2)))
        else:
            cost = 0
        self.total_spent += cost

        print(f"Upgraded to level {self.upgrade_level} ({self.chosen_path})")

        self.range_image = pg.Surface((self.range * 2, self.range * 2), pg.SRCALPHA)
        self.range_image.fill((0, 0, 0, 0))
        pg.draw.circle(self.range_image, (255, 255, 255, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center

    def _upgrade_cadence(self):
        global _cadence_sound_channel
        if self.upgrade_level < len(self.data):
            self.upgrade_level += 1
            level_data = self.data[self.upgrade_level - 1]

            cost = int(c.UPGRADE_CADENCE_BASE_COST * (c.UPGRADE_GROWTH_FACTOR_CADENCE ** (self.upgrade_level - 2)))
            self.total_spent += cost
            self.range = level_data.get("range", self.range)
            self.cooldown = level_data.get("cooldown", 0)
            self.damage = level_data.get("damage", 0)

            self.original_image = self.sprite_sheets[self.upgrade_level - 1]
            self.animation_list = [self.original_image]
            self.image = self.original_image

            self.frame_index = 0
            print(f"Upgraded to level {self.upgrade_level}")

            self.range_image = pg.Surface((self.range * 2, self.range * 2), pg.SRCALPHA)
            self.range_image.fill((0, 0, 0, 0))
            pg.draw.circle(self.range_image, (255, 255, 255, 100), (self.range, self.range), self.range)
            self.range_rect = self.range_image.get_rect()
            self.range_rect.center = self.rect.center

            self.speed_buff = level_data.get("speed_buff", self.speed_buff)
            if _cadence_sound_channel:
                _cadence_sound_channel.stop()
                _cadence_sound_channel = None

            sound_key = f"cadence_song_{self.upgrade_level}"
            if not sound_cache.mute_music and sound_key in sound_cache.SOUND_CACHE:
                _cadence_sound_channel = sound_cache.SOUND_CACHE[sound_key].play(loops=-1)
                if _cadence_sound_channel:
                    _cadence_sound_channel.set_volume(0.3)
                    sound_cache.register_cadence_channel(_cadence_sound_channel)
        else:
            print("Tower already at max level")

    def apply_monk_stun(self, enemy):
        if self.upgrade_level != 4:
            return
        if self.tower_type != "monk":
            return
        if self.chosen_path != "path_a":
            return

        now = pg.time.get_ticks()

        if now - self.last_lightning_hit_time > c.DRAGON_SAGE_MARK_RESET_TIME:
            self.lightning_combo = 0

        self.last_lightning_hit_time = now
        self.lightning_combo += 1

        if self.lightning_combo >= c.DRAGON_SAGE_MARKS_REQUIRED:
            if now - enemy.last_dragon_stun_time >= c.DRAGON_SAGE_STUN_COOLDOWN:
                enemy.stunned = True
                enemy.stun_end_time = now + c.DRAGON_SAGE_STUN_DURATION
                enemy.last_dragon_stun_time = now
                play_sound("monk-stun")

            self.lightning_combo = 0

    def draw(self, surface):
        rotated = pg.transform.rotate(self.original_image, self.angle)
        self.rect = rotated.get_rect(center=(self.x, self.y))

        surface.blit(rotated, self.rect)

        #draw range circle only when selected
        if getattr(self, "selected", False):
            surface.blit(self.range_image, self.range_rect)

        #soul rip effects
        if self.tower_type == "warrior" and self.chosen_path == "path_b":
            now = pg.time.get_ticks()

            if self.is_buffed:
                pulse_timer = now % 600
                progress = pulse_timer / 600.0
                wave_radius = int(15 + (progress * 22))
                wave_surf = pg.Surface((wave_radius * 2, wave_radius * 2), pg.SRCALPHA)
                alpha = int(255 * (1.0 - progress))
                pg.draw.circle(wave_surf, (180, 70, 255, alpha), (wave_radius, wave_radius), wave_radius, 2)
                surface.blit(wave_surf, (int(self.x - wave_radius), int(self.y - wave_radius)))

                for i in range(4):
                    ember_loop = (now + (i * 250)) % 1000
                    ember_prog = ember_loop / 1000.0

                    offset_y = int(ember_prog * 28)
                    offset_x = [-12, 10, -4, 8][i]

                    ex = int(self.x + offset_x)
                    ey = int(self.y + 10 - offset_y)

                    ember_alpha = int(255 * (1.0 - ember_prog))

                    ember_surf = pg.Surface((3, 3), pg.SRCALPHA)
                    ember_surf.fill((235, 130, 255, ember_alpha))
                    surface.blit(ember_surf, (ex, ey))

            elif self.soul_runes > 0:
                for i in range(self.soul_runes):
                    orbit_speed = 0.0015
                    angle = (now * orbit_speed) + (i * (2 * math.pi / self.max_soul_runes))

                    radius = 25 + int(3 * math.sin(now * 0.004 + i))
                    rx = self.x + math.cos(angle) * radius
                    ry = self.y + math.sin(angle) * radius

                    rune_size = 4
                    sigil_points = [
                        (rx, ry - rune_size),
                        (rx + rune_size, ry),
                        (rx, ry + rune_size),
                        (rx - rune_size, ry)
                    ]

                    pg.draw.polygon(surface, (110, 30, 200), sigil_points)
                    pg.draw.polygon(surface, (210, 150, 255), sigil_points, 1)
                    pg.draw.circle(surface, (255, 255, 255), (int(rx), int(ry)), 1)

    def reset_buffs(self):
        self.cooldown_buff = 1.0

    def apply_buffs(self, cooldown_buff=1.0):
        self.cooldown_buff *= cooldown_buff

    @property
    def effective_cooldown(self):
        base_cd = self.cooldown * self.cooldown_buff

        if self.tower_type == "warrior" and self.chosen_path == "path_b" and self.is_buffed:
            base_cd *= 0.50

        return max(100, base_cd)

    def prepare_chain_attack(self, initial_target):
        self.chain_hits = [initial_target]
        self.chain_index = 0
        self.chain_start_time = pg.time.get_ticks()
        self.attacking = True
        self.frame_index = 0
        self.damage_dealt = 0

    def update_cadence_volume(self):
        global _cadence_sound_channel
        if _cadence_sound_channel:
            volume = 0.0 if sound_cache.mute_music else 0.3
            _cadence_sound_channel.set_volume(volume)

    def sync_rect(self):
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)