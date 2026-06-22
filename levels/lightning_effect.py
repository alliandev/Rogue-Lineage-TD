import pygame as pg
import random
import math

class LightningEffect:
    def __init__(self, start_pos, enemy, travel_time=None):
        self.start_pos = start_pos
        self.enemy = enemy

        self.start_time = pg.time.get_ticks()
        self.travel_time = travel_time if travel_time is not None else 140
        self.linger_time = 120
        self.fade_time = 280

        self.duration = self.travel_time + self.linger_time + self.fade_time
        self.finished = False

        self.segments = 12
        self.max_offset = 22

        self.points = []
        self.branches = []
        self.end_pos = None

        if self.enemy and self.enemy.alive():
            self.generate_points()

    def generate_points(self):
        dx = self.enemy.rect.centerx - self.start_pos[0]
        dy = self.enemy.rect.centery - self.start_pos[1]
        distance = max(1, math.hypot(dx, dy))

        self.end_pos = (int(self.enemy.rect.centerx), int(self.enemy.rect.centery))

        self.max_offset = min(28, distance * 0.2)
        self.points = self._build_bolt(self.start_pos, self.end_pos, self.segments, self.max_offset)

    def _build_bolt(self, start, end, segments, max_offset):
        points = [start, end]

        iterations = 4
        roughness = 0.6  # each iteration displaces this much less than the previous

        for i in range(iterations):
            scale = max_offset * (roughness ** i)
            new_points = []

            for j in range(len(points) - 1):
                p1 = points[j]
                p2 = points[j + 1]

                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2

                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                seg_len = max(1, math.hypot(dx, dy))

                # fresh perpendicular each time, no accumulated drift
                perp_x = -dy / seg_len
                perp_y = dx / seg_len

                displacement = random.uniform(-scale, scale)

                mid_x += perp_x * displacement
                mid_y += perp_y * displacement

                new_points.append(p1)
                new_points.append((mid_x, mid_y))

            new_points.append(points[-1])
            points = new_points

        return points

    def update(self):
        elapsed = pg.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.finished = True

    def draw(self, surface):
        if self.finished or not self.points:
            return

        elapsed = pg.time.get_ticks() - self.start_time

        # OUTWARD TRAVEL
        if elapsed < self.travel_time:
            progress = elapsed / self.travel_time
            visible_points = self.points[:max(2, int(len(self.points) * progress))]
            alpha = 255
            branch_progress = progress
            retract = False

        # FULL BOLT LINGER
        elif elapsed < self.travel_time + self.linger_time:
            visible_points = self.points
            alpha = 255
            branch_progress = 1.0
            retract = False

        # FADE OUT — retract from tower end toward enemy
        else:
            fade_elapsed = elapsed - (self.travel_time + self.linger_time)
            progress = fade_elapsed / self.fade_time
            cutoff = int(progress * len(self.points))
            visible_points = self.points[cutoff:]
            alpha = 255
            branch_progress = 1.0
            retract = True

        if len(visible_points) < 2:
            return

        temp = pg.Surface(surface.get_size(), pg.SRCALPHA)

        # main bolt
        pg.draw.lines(temp, (0, 220, 255, max(0, int(alpha * 0.8))), False, visible_points, 7)
        pg.draw.lines(temp, (255, 255, 255, alpha), False, visible_points, 4)

        surface.blit(temp, (0, 0))

        surface.blit(temp, (0, 0))

        # --- LAYER 1: thin cyan outer border ---
        pg.draw.lines(temp, (0, 220, 255, max(0, int(alpha * 0.8))), False, visible_points, 7)

        # --- LAYER 2: thick white core ---
        pg.draw.lines(temp, (255, 255, 255, alpha), False, visible_points, 4)

        # --- BRANCHES ---
        if branch_progress >= 0.5:
            branch_alpha = min(alpha, int(alpha * (branch_progress - 0.5) * 2))
            for branch in self.branches:
                if len(branch) >= 2:
                    pg.draw.lines(temp, (0, 220, 255, branch_alpha), False, branch, 1)


        surface.blit(temp, (0, 0))