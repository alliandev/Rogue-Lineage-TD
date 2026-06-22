import pygame as pg
import constants as c

COL_BG          = (248, 248, 248, 240)
COL_HEADER      = (235, 235, 235, 255)
COL_DIVIDER     = (190, 190, 190, 255)
COL_TEXT        = (25, 25, 25)
COL_TEXT_DIM    = (90, 90, 90)
COL_SILVER      = (140, 145, 160)
COL_UPGRADE_A   = (100, 155, 235, 255)
COL_UPGRADE_B   = (220, 95, 95, 255)
COL_UPGRADE_MAX = (225, 185, 70, 255)
COL_LOCKED      = (170, 170, 170, 255)
COL_RED         = (200, 70, 70)

PANEL_W = 220
PANEL_H = 406

UPGRADE_INFO = {
    "warrior": {
        "path_a": [
            {"name": "Warrior Training",       "desc": "Training comes with a fresh new helmet."},
            {"name": "Flame Charge",           "desc": "Imbues your sword with a fierce flame, dealing extra damage."},
            {"name": "Sealed Sword",           "desc": "Pull the legendary sword from the Sealed Church, unlocking powerful white flames and a faster swingspeed."},
        ],
        "path_b": [
            {"name": "Wraith Knight Training", "desc": "Training comes with an evil new helmet."},
            {"name": "Darkflame Burst",        "desc": "Imbues your sword with dark fire, applying Sealing Flames for five seconds"},
            {"name": "Soul Rip",               "desc": "Gain runes on your arm for each enemy killed which can be used for a temporary buff."},
        ],
    },
    "druid": {
        "path_a": [
            {"name": "Botany Training", "desc": "Draws on natural energy to deal more elemental damage."},
            {"name": "Philo Stone",     "desc": "Unlock the potential found in the philosophers stone to cast spells faster."},
            {"name": "Percutiens",      "desc": "Learn a powerful lightning spell that deals heavy elemental damage."},
        ],
        "path_b": [
            {"name": "Illusion Mastery","desc": "Tap into the subconscious for quicker spell casting."},
            {"name": "Intermissum",     "desc": "Spells have a chance to apply an insanity at random, debuffing enemies."},
            {"name": "Percutiens",      "desc": "Learn a powerful lightning spell that deals heavy elemental damage."},
        ],
    },
    "thief": {
        "path_a": [
            {"name": "Mythril Dagger",    "desc": "A lighter, sharper blade allows for deadlier attacks."},
            {"name": "Assassin Training", "desc": "Training comes with a fresh new helmet."},
            {"name": "Chain Lethality",   "desc": "Slower but stronger attacks now leap between nearby enemies."},
        ],
        "path_b": [
            {"name": "Tanto Dagger",      "desc": "A longer, sharper blade allows for further reaching attacks."},
            {"name": "Agility",           "desc": "Refined movement lets attacks come out noticeably faster."},
            {"name": "Lethality",         "desc": "A relentless flurry of fast single-target strikes."},
        ],
    },
    "monk": {
        "path_a": [
            {"name": "Chi Blocking",    "desc": "Learn the various pressure points in enemies, dealing more damage."},
            {"name": "Monastic Stance", "desc": "Perfect your form through disciplined training for an extra damage and speed boost."},
            {"name": "Dragon Sage",     "desc": "Vanquish your enemies with the immense force born from a dragon, every fifth attack stuns an enemy."},
        ],
        "path_b": [
            {"name": "Trained Combat",  "desc": "Wrapped fists strike with noticeably more force."},
            {"name": "Spin Kick",       "desc": "A swift spinning kick that has a chance to slow an enemy."},
            {"name": "Oni Armor",       "desc": "Become an unstoppable force, dealing increased damage with every strike."},
        ],
    },
}

PATH_CHOICE_INFO = {
    "warrior": {
        "path_a": {"name": "Sigil Knight",  "desc": "Cleanse the world of Ardor's influence, utilizing unique elemental charges."},
        "path_b": {"name": "Wraith Knight", "desc": "Break your bonds with the Sigil Knight Order, collect runes from enemies for buffs."},
    },
    "druid": {
        "path_a": {"name": "Druid",         "desc": "Slow, heavy-hitting elemental magic."},
        "path_b": {"name": "Illusionist",   "desc": "Faster casting  with a shorter cooldown."},
    },
    "thief": {
        "path_a": {"name": "Faceless Order","desc": "Slow but devastating attacks chain across several enemies."},
        "path_b": {"name": "Shinobi",       "desc": "Extremely fast and damaging single-target strikes."},
    },
    "monk": {
        "path_a": {"name": "Dragon Sage",   "desc": "Mark enemies with lightning, stunning them on the fifth hit."},
        "path_b": {"name": "Oni",           "desc": "Specialize in raw striking power with no stun."},
    },
}

TOWER_DISPLAY_NAME = {
    "warrior": "Warrior",
    "druid":   "Scholar",
    "cadence": "Cadence",
    "thief":   "Thief",
    "monk":    "Brawler",
}


def _get_upgrade_cost(tower):
    tt = tower.tower_type
    lvl = tower.upgrade_level
    if tt == "warrior":  return c.get_warrior_upgrade_cost(c.UPGRADE_WARRIOR_BASE_COST, lvl)
    if tt == "druid":    return c.get_druid_upgrade_cost(c.UPGRADE_DRUID_BASE_COST, lvl)
    if tt == "cadence":  return c.get_cadence_upgrade_cost(c.UPGRADE_CADENCE_BASE_COST, lvl)
    if tt == "thief":    return c.get_thief_upgrade_cost(c.UPGRADE_THIEF_BASE_COST, lvl)
    if tt == "monk":     return c.get_monk_upgrade_cost(c.UPGRADE_MONK_BASE_COST, lvl)
    return 0


def _get_max_level(tower):
    tt = tower.tower_type
    if tt == "warrior":  return c.WARRIOR_LEVELS
    if tt == "druid":    return c.DRUID_LEVELS
    if tt == "cadence":  return c.CADENCE_LEVELS
    if tt == "thief":    return c.THIEF_LEVELS
    if tt == "monk":     return c.MONK_LEVELS
    return 1


def _wrap(text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class TowerPanel:
    def __init__(self, cursor_images: dict, silver_image):
        self.cursor_images = cursor_images
        self.silver_image = silver_image

        pg.font.init()
        self.font_title = pg.font.Font("../assets/fonts/HWYGOTH.TTF", 15)
        self.font_body  = pg.font.Font("../assets/fonts/HWYGOTH.TTF", 11)
        self.font_cost  = pg.font.Font("../assets/fonts/SourceSansPro-Semibold.ttf", 13)
        self.font_label = pg.font.Font("../assets/fonts/HWYGOTH.TTF", 10)
        self.font_icon  = pg.font.Font("../assets/fonts/SourceSansPro-Semibold.ttf", 8)

        self.upgrade_btn_rect_a = None
        self.upgrade_btn_rect_b = None
        self.sell_btn_rect = None

        self._slide_x    = 0.0
        self._visible    = False
        self.SLIDE_SPD   = 0.12

        self._flash_timer    = 0
        self._flash_duration = 120
        self._last_tower     = None

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False
        self.upgrade_btn_rect_a = None
        self.upgrade_btn_rect_b = None
        self.sell_btn_rect = None

    def draw(self, surface, tower, silver: int) -> bool:
        target = 1.0 if (self._visible and tower) else 0.0
        self._slide_x += (target - self._slide_x) * self.SLIDE_SPD
        if abs(self._slide_x - target) < 0.01:
            self._slide_x = target

        if self._slide_x < 0.01:
            self.upgrade_btn_rect_a = None
            self.upgrade_btn_rect_b = None
            self.sell_btn_rect = None
            self._last_tower = None
            return False

        if not self._last_tower and not tower:
            return False

        if tower:
            self._last_tower = tower
        draw_tower = tower if tower else self._last_tower

        panel_x = int(c.SCREEN_WIDTH - PANEL_W * self._slide_x)
        panel_y = 0

        panel_surf = pg.Surface((PANEL_W, PANEL_H), pg.SRCALPHA)
        panel_surf.fill(COL_BG)
        pg.draw.rect(panel_surf, COL_DIVIDER, (0, 0, PANEL_W, PANEL_H), 1)

        header_h = 56
        pg.draw.rect(panel_surf, COL_HEADER, (0, 0, PANEL_W, header_h))
        pg.draw.line(panel_surf, COL_DIVIDER, (0, header_h), (PANEL_W, header_h), 1)

        icon_size = 40
        icon_x, icon_y = 8, 8
        tt = draw_tower.tower_type
        if tt in self.cursor_images:
            raw  = self.cursor_images[tt]
            icon = pg.transform.smoothscale(raw, (icon_size, icon_size))
            panel_surf.blit(icon, (icon_x, icon_y))

        name    = TOWER_DISPLAY_NAME.get(tt, tt.title())
        max_lvl = _get_max_level(draw_tower)
        lvl_str = f"Lv {draw_tower.upgrade_level}/{max_lvl}"
        name_s  = self.font_title.render(name,    True, COL_TEXT)
        lvl_s   = self.font_label.render(lvl_str, True, COL_TEXT_DIM)
        text_x  = icon_x + icon_size + 8
        panel_surf.blit(name_s, (text_x, 10))
        panel_surf.blit(lvl_s,  (text_x, 10 + name_s.get_height() + 2))

        stats_y = header_h + 8
        stats   = [
            ("DMG", str(draw_tower.damage)),
            ("RNG", str(draw_tower.range)),
            ("CD",  str(draw_tower.cooldown)),
        ]
        col_w = PANEL_W // len(stats)
        for i, (label, val) in enumerate(stats):
            lx = i * col_w + col_w // 2
            ls = self.font_label.render(label, True, COL_TEXT_DIM)
            vs = self.font_cost.render(val,    True, COL_TEXT)
            panel_surf.blit(ls, (lx - ls.get_width() // 2, stats_y))
            panel_surf.blit(vs, (lx - vs.get_width() // 2, stats_y + ls.get_height() + 1))

        pg.draw.line(panel_surf, COL_DIVIDER,
                     (8, stats_y + 30), (PANEL_W - 8, stats_y + 30), 1)

        path_y    = stats_y + 38
        maxed     = draw_tower.upgrade_level >= max_lvl
        has_paths = tt != "cadence"
        needs_choice = has_paths and getattr(draw_tower, "chosen_path", None) is None

        self.upgrade_btn_rect_a = None
        self.upgrade_btn_rect_b = None
        self.sell_btn_rect = None
        self._choice_btn_rect_a = None
        self._choice_btn_rect_b = None
        sell_rect_local = None

        if needs_choice:
            path_y = self._draw_path_choice(panel_surf, draw_tower, tt, silver, path_y)
        else:
            path_y, sell_rect_local = self._draw_active_path(panel_surf, draw_tower, tt, silver, path_y, maxed, max_lvl)

        old_clip = surface.get_clip()
        surface.set_clip(pg.Rect(0, 0, c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        surface.blit(panel_surf, (panel_x, panel_y))
        surface.set_clip(old_clip)

        if self._choice_btn_rect_a:
            self.upgrade_btn_rect_a = self._choice_btn_rect_a.move(panel_x, panel_y)
        if self._choice_btn_rect_b:
            self.upgrade_btn_rect_b = self._choice_btn_rect_b.move(panel_x, panel_y)

        if not needs_choice and hasattr(self, "_active_btn_rect"):
            self.upgrade_btn_rect_a = self._active_btn_rect.move(panel_x, panel_y) if self._active_btn_rect else None

        if sell_rect_local:
            self.sell_btn_rect = sell_rect_local.move(panel_x, panel_y)

        return False

    def _draw_path_choice(self, panel_surf, draw_tower, tt, silver, path_y):
        choice_label = self.font_label.render("CHOOSE YOUR PATH  (free)", True, COL_TEXT_DIM)
        panel_surf.blit(choice_label, (8, path_y))
        path_y += choice_label.get_height() + 6

        info = PATH_CHOICE_INFO.get(tt, {})

        card_h = 96
        card_w = PANEL_W - 16

        card_a = pg.Rect(8, path_y, card_w, card_h)
        self._draw_path_card(panel_surf, card_a, COL_UPGRADE_A, True,
                             info.get("path_a", {"name": "Path A", "desc": ""}), None)

        path_y = card_a.bottom + 8

        card_b = pg.Rect(8, path_y, card_w, card_h)
        self._draw_path_card(panel_surf, card_b, COL_UPGRADE_B, True,
                             info.get("path_b", {"name": "Path B", "desc": ""}), None)

        self._choice_btn_rect_a = card_a
        self._choice_btn_rect_b = card_b

        return card_b.bottom + 8

    def _draw_path_card(self, panel_surf, rect, accent_col, can_afford, info, cost):
        card_surf = pg.Surface((rect.width, rect.height))

        if can_afford:
            bg_col = (
                min(255, 235 + (accent_col[0] - 235) // 6),
                min(255, 238 + (accent_col[1] - 238) // 6),
                min(255, 242 + (accent_col[2] - 242) // 6),
            )
        else:
            bg_col = (232, 232, 232)

        card_surf.fill(bg_col)

        border_col = accent_col[:3] if can_afford else COL_LOCKED[:3]
        pg.draw.rect(card_surf, border_col, (0, 0, rect.width, rect.height), 2, border_radius=4)

        name_s = self.font_title.render(info["name"], True, COL_TEXT if can_afford else COL_TEXT_DIM)
        card_surf.blit(name_s, (8, 6))

        desc_lines = _wrap(info["desc"], self.font_body, rect.width - 16)
        dy = 6 + name_s.get_height() + 4
        for line in desc_lines:
            ls = self.font_body.render(line, True, COL_TEXT_DIM)
            card_surf.blit(ls, (8, dy))
            dy += ls.get_height() + 1

        if cost is None:
            cost_col = COL_UPGRADE_A if accent_col == COL_UPGRADE_A else COL_UPGRADE_B
            cost_s = self.font_cost.render("FREE", True, cost_col[:3])
            cost_x = rect.width - cost_s.get_width() - 8
            cost_y = rect.height - cost_s.get_height() - 6
            card_surf.blit(cost_s, (cost_x, cost_y))
        else:
            cost_col = COL_TEXT if can_afford else COL_RED
            cost_s = self.font_cost.render(f"{cost}", True, cost_col)
            cost_x = rect.width - cost_s.get_width() - 8
            cost_y = rect.height - cost_s.get_height() - 6

            if self.silver_image:
                icon = pg.transform.smoothscale(self.silver_image, (14, 14))
                icon_x = cost_x - 18
                card_surf.blit(icon, (icon_x, cost_y - 1))

            card_surf.blit(cost_s, (cost_x, cost_y))

        panel_surf.blit(card_surf, rect.topleft)

    def _draw_active_path(self, panel_surf, draw_tower, tt, silver, path_y, maxed, max_lvl):
        chosen = getattr(draw_tower, "chosen_path", None)
        info_list = []
        if tt in UPGRADE_INFO and chosen in ("path_a", "path_b"):
            info_list = UPGRADE_INFO[tt].get(chosen, [])
        elif tt == "cadence":
            info_list = [
                {"name": "Sweet Soothing", "desc": "A masterfully crafted trumpet empowers your troops."},
                {"name": "Joyous Dance",   "desc": "Perform a faster-paced tune to further motivate troops."},
            ]

        path_idx = max(0, draw_tower.upgrade_level - 1)
        if maxed:
            upg = {"name": "MAX", "desc": "Fully upgraded."}
        elif 0 <= path_idx < len(info_list):
            upg = info_list[path_idx]
        else:
            upg = {"name": "MAX", "desc": "Fully upgraded."}

        label_text = "UPGRADE PATH"
        if chosen == "path_a":
            label_text = "PATH A"
        elif chosen == "path_b":
            label_text = "PATH B"

        path_label = self.font_label.render(label_text, True, COL_TEXT_DIM)
        panel_surf.blit(path_label, (8, path_y))
        path_y += path_label.get_height() + 4

        accent = COL_UPGRADE_B if chosen == "path_b" else COL_UPGRADE_A
        upg_name_col = COL_UPGRADE_MAX if maxed else accent
        upg_name_s   = self.font_title.render(upg["name"], True, upg_name_col)
        panel_surf.blit(upg_name_s, (8, path_y))
        path_y += upg_name_s.get_height() + 3

        desc_lines = _wrap(upg["desc"], self.font_body, PANEL_W - 16)
        for line in desc_lines:
            ls = self.font_body.render(line, True, COL_TEXT_DIM)
            panel_surf.blit(ls, (8, path_y))
            path_y += ls.get_height() + 1
        path_y += 6

        pip_r      = 5
        pip_gap    = 14
        total_pips = max_lvl
        track_w    = total_pips * pip_gap - (pip_gap - pip_r * 2)
        pip_start  = (PANEL_W - track_w) // 2
        for p in range(total_pips):
            px     = pip_start + p * pip_gap + pip_r
            filled = p < draw_tower.upgrade_level
            col    = accent if filled else COL_LOCKED
            pg.draw.circle(panel_surf, col, (px, path_y + pip_r), pip_r)
            if filled:
                pg.draw.circle(panel_surf, (200, 255, 200), (px, path_y + pip_r), pip_r - 2)
        path_y += pip_r * 2 + 10

        btn_h          = 30
        btn_y          = path_y
        btn_rect_local = pg.Rect(8, btn_y, PANEL_W - 16, btn_h)

        now          = pg.time.get_ticks()
        flash_active = (now - self._flash_timer) < self._flash_duration
        flash_t      = max(0.0, 1.0 - (now - self._flash_timer) / self._flash_duration)

        if maxed:
            btn_col      = COL_UPGRADE_MAX
            btn_text     = "MAXED OUT"
            btn_text_col = (20, 20, 20)
            self._active_btn_rect = None
        else:
            cost       = _get_upgrade_cost(draw_tower)
            can_afford = silver >= cost
            base_col   = accent if can_afford else COL_RED
            if flash_active and can_afford:
                r = int(base_col[0] + (255 - base_col[0]) * flash_t * 0.4)
                g = int(base_col[1] + (255 - base_col[1]) * flash_t * 0.4)
                b = int(base_col[2] + (255 - base_col[2]) * flash_t * 0.4)
                btn_col = (r, g, b, 255)
            else:
                btn_col = base_col
            btn_text     = f"Upgrade  {cost}"
            btn_text_col = COL_TEXT
            self._active_btn_rect = btn_rect_local

        pg.draw.rect(panel_surf, btn_col, btn_rect_local, border_radius=4)
        pg.draw.rect(panel_surf, COL_DIVIDER, btn_rect_local, 1, border_radius=4)

        if not maxed and self.silver_image:
            icon = pg.transform.smoothscale(self.silver_image, (16, 16))
            icon_rect = icon.get_rect()
            icon_rect.center = (btn_rect_local.x + 14, btn_rect_local.centery)
            panel_surf.blit(icon, icon_rect)

        btn_s = self.font_cost.render(btn_text, True, btn_text_col)
        panel_surf.blit(btn_s, (btn_rect_local.centerx - btn_s.get_width() // 2,
                                btn_rect_local.centery - btn_s.get_height() // 2))
        path_y += btn_h + 6

        refund = int(getattr(draw_tower, "total_spent", 0) * c.REFUND_PERCENTAGE)
        sell_rect_local = pg.Rect(8, path_y, PANEL_W - 16, btn_h)

        pg.draw.rect(panel_surf, (185, 60, 55), sell_rect_local, border_radius=4)
        pg.draw.rect(panel_surf, (220, 100, 90), sell_rect_local, 1, border_radius=4)

        if self.silver_image:
            icon = pg.transform.smoothscale(self.silver_image, (14, 14))
            panel_surf.blit(icon, (sell_rect_local.x + 8, sell_rect_local.centery - 7))

        sell_s = self.font_cost.render(f"Sell  +{refund}", True, (255, 230, 220))
        panel_surf.blit(sell_s, (sell_rect_local.centerx - sell_s.get_width() // 2,
                                 sell_rect_local.centery - sell_s.get_height() // 2))
        path_y += btn_h + 8

        return path_y, sell_rect_local

    def handle_event(self, event, tower, silver, on_upgrade, on_choose_path=None, on_sell=None):
        if event.type != pg.MOUSEBUTTONDOWN or event.button != 1:
            return
        if not tower:
            return

        needs_choice = (
            tower.tower_type != "cadence"
            and getattr(tower, "chosen_path", None) is None
        )

        if needs_choice:
            if self.upgrade_btn_rect_a and self.upgrade_btn_rect_a.collidepoint(event.pos):
                if on_choose_path:
                    on_choose_path(tower, "path_a", 0)
                    self._flash_timer = pg.time.get_ticks()
                return
            if self.upgrade_btn_rect_b and self.upgrade_btn_rect_b.collidepoint(event.pos):
                if on_choose_path:
                    on_choose_path(tower, "path_b", 0)
                    self._flash_timer = pg.time.get_ticks()
                return
            return

        if self.sell_btn_rect and self.sell_btn_rect.collidepoint(event.pos):
            if on_sell:
                on_sell(tower)
            return

        if not self.upgrade_btn_rect_a:
            return
        if self.upgrade_btn_rect_a.collidepoint(event.pos):
            max_lvl = _get_max_level(tower)
            if tower.upgrade_level < max_lvl:
                cost = _get_upgrade_cost(tower)
                if silver >= cost:
                    on_upgrade(tower, cost)
                    self._flash_timer = pg.time.get_ticks()