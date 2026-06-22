import pygame as pg
import json
import xml.etree.ElementTree as ET
import world
from tower import Tower
from enemy import Enemy
from button import Button
import constants as c
import math
from warrior_data import WARRIOR_DATA
from druid_data import DRUID_DATA
from cadence_data import CADENCE_DATA
from thief_data import THIEF_DATA
from monk_data import MONK_DATA
import cv2
import numpy as np
import sys
import random
import sound_cache
from tower import play_sound
import time
from enemy import Enemy, Necromancer
from tower_panel import TowerPanel

played_death_sound = False
fast_forward_enabled = False

smooth_x = 0
smooth_y = 0
snap_initialized = False

# --- Helper for converting OpenCV frame to Pygame surface ---
def opencv_frame_to_surface(frame):
    frame = cv2.flip(frame, 1)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    frame = pg.surfarray.make_surface(frame)
    return frame

# --- Function to play video ---
def play_video(screen, video_path, loop=False):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Failed to open video: {video_path}")
        sys.exit()

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 60
    frame_delay = 800 / video_fps
    last_frame_time = pg.time.get_ticks()

    clock = pg.time.Clock()

    while True:
        now = pg.time.get_ticks()
        if now - last_frame_time >= frame_delay:
            ret, frame = cap.read()
            if not ret:
                if loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        break
                else:
                    break

            frame_surface = opencv_frame_to_surface(frame)
            frame_surface = pg.transform.scale(frame_surface, screen.get_size())
            screen.blit(frame_surface, (0, 0))
            pg.display.flip()

            last_frame_time = now

        for event in pg.event.get():
            if event.type == pg.QUIT:
                cap.release()
                pg.quit()
                sys.exit()

        clock.tick(60)

    cap.release()


def main_menu(screen):
    prev_hover_index = -1
    options_mode = False
    mute_music = sound_cache.mute_music
    mute_sfx = sound_cache.mute_sfx
    sound_cache.set_mute_music(mute_music)
    sound_cache.set_mute_sfx(mute_sfx)

    pg.mixer.music.load("../assets/audio/theme.wav")
    pg.mixer.music.play(-1)

    def load_arrow_images(sprite_sheet):
        frame_rects = [
            pg.Rect(0, 0, 81, 48),
            pg.Rect(80, 0, 67, 48),
            pg.Rect(146, 0, 64, 48),
            pg.Rect(209, 0, 91, 48),
            pg.Rect(295, 0, 85, 48),
            pg.Rect(0, 0, 81, 48),
        ]
        return [sprite_sheet.subsurface(rect).copy() for rect in frame_rects]

    arrow_sheet = pg.image.load("../levels/arrow_animation.png").convert_alpha()
    arrow_frames = load_arrow_images(arrow_sheet)
    arrow_frame_index = 0
    arrow_frame_timer = 0
    arrow_frame_delay = 100

    play_video(screen, "intro.mp4", loop=False)

    menu_items = ["PLAY", "OPTIONS", "CREDITS"]
    selected_index = 0

    font = pg.font.Font("../assets/fonts/Roquen DEMO.otf", 17)
    highlight_color = (255, 255, 255)
    normal_color = (160, 160, 160)

    clock = pg.time.Clock()

    background_videos = [f"background_{i}.mp4" for i in range(1, 7)]
    last_video = None

    def get_new_video(exclude=None):
        return random.choice([v for v in background_videos if v != exclude])

    current_video = get_new_video()
    cap = cv2.VideoCapture(current_video)
    if not cap.isOpened():
        print("Failed to open background video")
        sys.exit()

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 60
    frame_delay = 800 / video_fps
    last_frame_time = pg.time.get_ticks()

    arrow_x_offset = 20
    arrow_y = None
    arrow_velocity = 0.0
    target_arrow_y = None
    spring_constant = 0.35
    damping = 0.55

    if 'hover_alpha' not in locals():
        hover_alpha = [0.0 for _ in menu_items]

    box_width, box_height = 400, 250
    box_rect = pg.Rect(
        (screen.get_width() - box_width) // 2,
        (screen.get_height() - box_height) // 2,
        box_width,
        box_height
    )

    running = True
    while running:
        now = pg.time.get_ticks()
        if now - last_frame_time >= frame_delay:
            ret, frame = cap.read()
            if not ret:
                cap.release()
                last_video = current_video
                current_video = get_new_video(exclude=last_video)
                cap = cv2.VideoCapture(current_video)
                if not cap.isOpened():
                    print("Failed to open background video")
                    sys.exit()
                continue

            frame_surface = opencv_frame_to_surface(frame)
            frame_surface = pg.transform.scale(frame_surface, screen.get_size())
            screen.blit(frame_surface, (0, 0))
            last_frame_time = now

        mouse_pos = pg.mouse.get_pos()

        x_pos = 50
        start_y = screen.get_height() - 150
        y_spacing = 33
        item_rects = []

        fade_speed = 0.18

        for i, text in enumerate(menu_items):
            if i == selected_index:
                hover_alpha[i] = min(1.0, hover_alpha[i] + fade_speed)
            else:
                hover_alpha[i] = max(0.0, hover_alpha[i] - fade_speed)

            interp = hover_alpha[i]
            blended_color = (
                int(normal_color[0] + (highlight_color[0] - normal_color[0]) * interp),
                int(normal_color[1] + (highlight_color[1] - normal_color[1]) * interp),
                int(normal_color[2] + (highlight_color[2] - normal_color[2]) * interp),
            )

            outline_color = (0, 0, 0)
            main_color = blended_color

            text_outline = font.render(text, True, outline_color)
            text_main = font.render(text, True, main_color)

            rect = text_main.get_rect(topleft=(x_pos, start_y + i * y_spacing))

            if i == selected_index:
                target_arrow_y = rect.centery

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                screen.blit(text_outline, rect.move(dx, dy))

            screen.blit(text_main, rect)
            item_rects.append(rect)

        hovered_index = -1
        for idx, r in enumerate(item_rects):
            if r.collidepoint(mouse_pos):
                hovered_index = idx
                break

        if hovered_index != prev_hover_index and hovered_index != -1:
            sound_cache.SOUND_CACHE["ui_hover"].play()
            prev_hover_index = hovered_index

        selected_index = hovered_index if hovered_index != -1 else selected_index

        if arrow_y is None and target_arrow_y is not None:
            arrow_y = target_arrow_y
            arrow_velocity = 0.0

        if arrow_y is not None and target_arrow_y is not None:
            displacement = target_arrow_y - arrow_y
            acceleration = displacement * spring_constant
            arrow_velocity += acceleration
            arrow_velocity *= damping
            arrow_y += arrow_velocity

        if selected_index >= 0 and item_rects:
            arrow_image = arrow_frames[arrow_frame_index]
            selected_rect = item_rects[selected_index]
            arrow_rect = arrow_image.get_rect(midright=(selected_rect.left + arrow_x_offset, arrow_y - 4))
            screen.blit(arrow_image, arrow_rect)

        if options_mode:
            overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))

            pg.draw.rect(screen, (30, 30, 30), box_rect, border_radius=8)
            pg.draw.rect(screen, (100, 100, 100), box_rect, 2, border_radius=8)

            music_text = font.render(f"Mute Music: {'ON' if mute_music else 'OFF'}", True, (255, 255, 255))
            sfx_text = font.render(f"Mute SFX: {'ON' if mute_sfx else 'OFF'}", True, (255, 255, 255))
            music_rect = music_text.get_rect(center=(box_rect.centerx, box_rect.top + 70))
            sfx_rect = sfx_text.get_rect(center=(box_rect.centerx, box_rect.top + 130))
            screen.blit(music_text, music_rect)
            screen.blit(sfx_text, sfx_rect)

        pg.display.flip()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                cap.release()
                pg.quit()
                sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pg.mouse.get_pos()
                if options_mode:
                    if not box_rect.collidepoint(mx, my):
                        options_mode = False
                    elif music_rect.collidepoint(mx, my):
                        mute_music = not mute_music
                        sound_cache.set_mute_music(mute_music)
                        sound_cache.SOUND_CACHE["confirm"].play()
                    elif sfx_rect.collidepoint(mx, my):
                        mute_sfx = not mute_sfx
                        sound_cache.set_mute_sfx(mute_sfx)
                        sound_cache.SOUND_CACHE["confirm"].play()
                else:
                    if item_rects[selected_index].collidepoint(mouse_pos):
                        sound_cache.SOUND_CACHE["confirm"].play()
                        if selected_index == 0:
                            running = False
                        elif selected_index == 1:
                            options_mode = True
                        elif selected_index == 2:
                            show_credits(screen)

        clock.tick(60)

        arrow_frame_timer += clock.get_time()
        if arrow_frame_timer >= arrow_frame_delay:
            arrow_frame_timer = 0
            arrow_frame_index = (arrow_frame_index + 1) % len(arrow_frames)

    cap.release()
    pg.mixer.music.stop()

def show_credits(screen):
    clock = pg.time.Clock()
    font = pg.font.Font(None, 24)
    title_font = pg.font.Font(None, 36)

    credits_lines = [
        "CREDITS",
        "",
        "Inspired by Rogue Lineage, published by Monad Studio.",
        "Credits to the main developers of Rogue Lineage: Ragoozer, Arch_Mage, and Grimmkind.",
        "Sounds and models are based on their work.",
        "",
        "All other development, design, and implementation by:",
        "Allian"
    ]

    #back button
    back_button_rect = pg.Rect(30, screen.get_height() - 70, 100, 40)
    back_font = pg.font.Font(None, 28)
    back_text = back_font.render("Back", True, (255, 255, 255))

    #background box
    box_width, box_height = 600, 300
    box_surface = pg.Surface((box_width, box_height), pg.SRCALPHA)
    box_surface.fill((0, 0, 0, 180))

    running = True
    while running:
        screen.fill((0, 0, 0))
        screen.blit(box_surface, (
            screen.get_width() // 2 - box_width // 2,
            screen.get_height() // 2 - box_height // 2
        ))

        #render credits text
        for i, line in enumerate(credits_lines):
            current_font = title_font if i == 0 else font
            text_surface = current_font.render(line, True, (255, 255, 255))
            screen.blit(
                text_surface,
                (
                    screen.get_width() // 2 - text_surface.get_width() // 2,
                    screen.get_height() // 2 - box_height // 2 + 20 + i * 30
                )
            )

        #draw back button
        pg.draw.rect(screen, (50, 50, 50), back_button_rect, border_radius=5)
        screen.blit(back_text, back_button_rect.move(20, 8).topleft)

        pg.display.flip()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if back_button_rect.collidepoint(event.pos):
                    running = False  #return to main menu

        clock.tick(60)


def create_vignette_mask(width, height, max_alpha=180):
    vignette = pg.Surface((width, height), pg.SRCALPHA)
    center_x, center_y = width // 2, height // 2
    max_distance = (center_x**2 + center_y**2) ** 0.5

    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance = (dx**2 + dy**2) ** 0.5
            fade = max(0, 1 - distance / max_distance)
            alpha = int(fade * max_alpha)
            vignette.set_at((x, y), (0, 0, 0, alpha))

    return vignette


def show_death_screen(screen):
    global played_death_sound

    for name in ("cadence_song_1", "cadence_song_2", "cadence_song_3"):
        sound_cache.SOUND_CACHE[name].stop()

    pg.mixer.music.load("purgatory_song.wav")
    pg.mixer.music.set_volume(0.5)
    pg.mixer.music.play(-1)

    if played_death_sound:
        print("Death sound already played once, skipping sound playback.")
    else:
        played_death_sound = True

        original_mute_sfx = sound_cache.mute_sfx
        sound_cache.mute_sfx = False

        death_sound = sound_cache.SOUND_CACHE.get("death_sound")

        if death_sound:
            death_sound.set_volume(1.0)

            for i in range(pg.mixer.get_num_channels()):
                ch = pg.mixer.Channel(i)
                if ch.get_busy():
                    ch.stop()

            channel = pg.mixer.Channel(15)
            channel.play(death_sound)
        else:
            print("Death sound not found!")

        sound_cache.mute_sfx = original_mute_sfx

    play_video(screen, "wipe.mp4", loop=False)

    ferryman_sound = pg.mixer.Sound("ferryman.wav")
    ferryman_sound.play()

    wipe_img = pg.image.load("wipe.png").convert()
    wipe_img = pg.transform.scale(wipe_img, screen.get_size())

    font = pg.font.Font("../assets/fonts/HWYGOTH.TTF", 16)
    bold_font = pg.font.Font("../assets/fonts/HWYGWDE.TTF", 20)
    clock = pg.time.Clock()

    overlay_width = 460
    overlay_height = 100
    overlay_rect = pg.Rect(
        screen.get_width() // 2 - overlay_width // 2,
        screen.get_height() // 2 - overlay_height // 2 + 150 - 30,
        overlay_width,
        overlay_height
    )

    overlay_surface = pg.Surface((overlay_rect.width, overlay_rect.height), pg.SRCALPHA)
    overlay_surface.fill((0, 0, 0, 180))
    vignette = create_vignette_mask(overlay_rect.width, overlay_rect.height, max_alpha=250)
    overlay_surface.blit(vignette, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

    button_width, button_height = 160, 40
    button_x = overlay_rect.x + 10 - 10
    button_y = overlay_rect.bottom + 10

    button_rect = pg.Rect(button_x, button_y, button_width, button_height)

    button_font = pg.font.Font("../assets/fonts/HWYGOTH.TTF", 14)
    button_text = button_font.render("Start New Game", True, (255, 255, 255))

    lines = [
        ("The Ferryman", bold_font),
        ("I'm very sorry to be the person to tell you", font),
        ("that you have perished.", font)
    ]

    waiting_for_click = True
    while waiting_for_click:
        screen.blit(wipe_img, (0, 0))
        screen.blit(overlay_surface, overlay_rect.topleft)

        for i, (text, current_font) in enumerate(lines):
            y_offset = -8 if i == 0 else 0
            screen.blit(
                current_font.render(text, True, (255, 255, 255)),
                (overlay_rect.x + 40, overlay_rect.y + 10 + i * font.get_height() + y_offset)
            )

        mouse_pos = pg.mouse.get_pos()

        if button_rect.collidepoint(mouse_pos):
            alpha = 240

        else:
            alpha = 150

        button_surface = pg.Surface((button_width, button_height), pg.SRCALPHA)
        button_surface.fill((0, 0, 0, alpha))
        button_vignette = create_vignette_mask(button_width, button_height, max_alpha=200)
        button_surface.blit(button_vignette, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
        screen.blit(button_surface, (button_x, button_y))

        text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, text_rect.topleft)

        pg.display.flip()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos):
                    pg.mixer.music.stop()
                    waiting_for_click = False
                    played_death_sound = False
                    return True

    clock.tick(60)
    pg.mixer.music.stop()
    return False

#initialize
pg.init()
clock = pg.time.Clock()
screen = pg.display.set_mode((c.SCREEN_WIDTH + c.SIDE_PANEL, c.SCREEN_HEIGHT))
pg.display.set_caption("Rogue Lineage TD")
pg.mixer.set_num_channels(32)
main_menu(screen)

#game variables
game_over = False
game_outcome = 0 #-1 is loss or 1 is win
level_started = False
last_enemy_spawn = pg.time.get_ticks()
placing_towers = False
selected_tower: Tower | None = None
selected_tower_type = None

#load images
#map
map_image = pg.image.load('../levels/deepforest_sketch_FINAL.png').convert_alpha()
#tower spritesheets
warrior_base_sheets = []
for x in range(1, c.WARRIOR_LEVELS + 1):
    warrior_base_sheets.append(pg.image.load(f'../assets/images/towers/warrior_animation_{x}.png').convert_alpha())

warrior_dsk_sheets = []
for x in range(1, 4):
    warrior_dsk_sheets.append(pg.image.load(f'../assets/images/towers/dsk_animation_{x}.png').convert_alpha())

warrior_spritesheets = {
    "base": warrior_base_sheets,
    "path_a": warrior_base_sheets,
    "path_b": warrior_dsk_sheets
}
druid_spritesheets = []
for x in range(1, c.DRUID_LEVELS + 1):
    druid_sheet = pg.image.load(f'../assets/images/towers/druid_animation_{x}.png').convert_alpha()
    druid_spritesheets.append(druid_sheet)
cadence_spritesheets = []
for x in range(1, c.CADENCE_LEVELS + 1):
    cadence_sheet = pg.image.load(f'../assets/images/towers/cadence_animation_{x}.png').convert_alpha()
    cadence_spritesheets.append(cadence_sheet)
thief_spritesheets = []
for x in range(1, c.THIEF_LEVELS + 1):
    thief_sheet = pg.image.load(f'../assets/images/towers/thief_animation_{x}.png').convert_alpha()
    thief_spritesheets.append(thief_sheet)
monk_spritesheets = []
for x in range(1, c.MONK_LEVELS + 1):
    monk_sheet = pg.image.load(f'../assets/images/towers/monk_animation_{x}.png').convert_alpha()
    monk_spritesheets.append(monk_sheet)



#individual tower images for mouse cursor
warrior_cursor_img = pg.image.load('../assets/images/towers/warrior.png').convert_alpha()
druid_cursor_img = pg.image.load('../assets/images/towers/druid.png').convert_alpha()
cadence_cursor_img = pg.image.load('../assets/images/towers/cadence.png').convert_alpha()
thief_cursor_img = pg.image.load('../assets/images/towers/thief.png').convert_alpha()
monk_cursor_img = pg.image.load('../assets/images/towers/monk.png').convert_alpha()

#necromancer animation sheets
necromancer_walk_sheet = pg.image.load('../assets/images/enemies/necro_animation-1.png').convert_alpha()
necromancer_summon_sheet = pg.image.load('../assets/images/enemies/necro_animation-2.png').convert_alpha()

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

#extract frames for necromancer animations
necromancer_walk_frames = extract_frames(necromancer_walk_sheet)
necromancer_summon_frames = extract_frames(necromancer_summon_sheet)

enemy_images = {
    "shrieker": pg.image.load('../assets/images/enemies/shrieker.png').convert_alpha(),
    "zscroom": pg.image.load('../assets/images/enemies/zscroom.png').convert_alpha(),
    "evil eye": pg.image.load('../assets/images/enemies/evil_eye.png').convert_alpha(),
    "howler": pg.image.load('../assets/images/enemies/howler.png').convert_alpha(),
    "sealed shrieker": pg.image.load('../assets/images/enemies/sealed_shrieker.png').convert_alpha(),
    "necromancer_walk": necromancer_walk_frames,
    "necromancer_summon": necromancer_summon_frames
}

#pillars
pillar_foreground = pg.image.load("pillar_foreground.png").convert_alpha()
#buttons
buy_warrior_image = pg.image.load('../assets/images/buttons/button_buy-warrior.png').convert_alpha()
buy_druid_image = pg.image.load('../assets/images/buttons/button_buy-druid.png').convert_alpha()
buy_cadence_image = pg.image.load('../assets/images/buttons/button_buy-cadence.png').convert_alpha()
buy_thief_image = pg.image.load('../assets/images/buttons/button_buy-thief.png').convert_alpha()
buy_dragonsage_image = pg.image.load('../assets/images/buttons/button_buy-monk.png').convert_alpha()
cancel_button_image = pg.image.load('../assets/images/buttons/button_cancel.png').convert_alpha()
begin_image = pg.image.load('../assets/images/buttons/begin.png').convert_alpha()
restart_image = pg.image.load('../assets/images/buttons/button_restart.png').convert_alpha()
fast_forward_image = pg.image.load('../assets/images/buttons/fast_forward.png').convert_alpha()
#gui
silver_image = pg.image.load('../assets/images/gui/silver.png').convert_alpha()
lives_wave_image = pg.image.load('../assets/images/gui/lives-wave.png').convert_alpha()
rogue_icon_image = pg.image.load('../assets/images/gui/rogue_icon.png').convert_alpha()

tower_panel = TowerPanel(
    {
        "warrior": warrior_cursor_img,
        "druid": druid_cursor_img,
        "cadence": cadence_cursor_img,
        "thief": thief_cursor_img,
        "monk": monk_cursor_img,
    },
    silver_image
)

#load level data
with open('../levels/deepforest_sketch_FINAL_final.tmj') as file:
    world_data = json.load(file)

#create the game world
game_world = world.World(world_data, map_image, enemy_images, clock)
game_world.process_data()
game_world.process_enemies()

#parse tileset xml
tileset_info = world_data["tilesets"][0]
tsx_filename = tileset_info["source"]
tsx_path = tsx_filename

tree = ET.parse(tsx_path)
tsx_root = tree.getroot()

display_width, display_height = pg.display.get_desktop_sizes()[0]

if display_height >= 1440:
    font_size = 26
    large_font_size = 48
elif display_height >= 1080:
    font_size = 24
    large_font_size = 42
else:
    font_size = 24
    large_font_size = 36

#load fonts
pg.font.init()
text_font = pg.font.Font("../assets/fonts/HWYGOTH.TTF", font_size)
large_font = pg.font.Font("../assets/fonts/HWYGOTH.TTF", large_font_size)
silver_font = pg.font.Font("../assets/fonts/SourceSansPro-Semibold.ttf", font_size)

#output text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def display_data():
    #draw panel
    pg.draw.rect(screen, "grey100", (c.SCREEN_WIDTH, 0, c.SIDE_PANEL, c.SCREEN_HEIGHT))
    pg.draw.rect(screen, "grey0", (c.SCREEN_WIDTH, 0, c.SIDE_PANEL, 400), 2)
    screen.blit(rogue_icon_image, (c.SCREEN_WIDTH, 235))
    pg.draw.rect(screen, "grey0", (c.SCREEN_WIDTH, 0, c.SIDE_PANEL, 500), 2)

    #display icons
    screen.blit(lives_wave_image, (180, 450))
    screen.blit(silver_image, (0, 458))

    #display health
    draw_text(str(game_world.health), text_font, "grey0", 207, 457)

    #display silver
    silver_text_1 = silver_font.render(str(game_world.silver), 0, "grey0")
    screen.blit(silver_text_1, (31, 458))
    silver_text_2 = silver_font.render(str(game_world.silver), 0, "grey100")
    screen.blit(silver_text_2, (30, 457))

    #display waves
    wave = max(0, min(game_world.level, 999))
    ones = wave % 10
    tens = (wave // 10) % 10
    hundreds = (wave // 100) % 10

    wave_y = 457
    ones_x = 297
    tens_x = 271
    hundreds_x = 245

    draw_text(str(hundreds), text_font, "grey0", hundreds_x, wave_y)
    draw_text(str(tens), text_font, "grey0", tens_x, wave_y)
    draw_text(str(ones), text_font, "grey0", ones_x, wave_y)

def can_place_tower(mouse_tile_x, mouse_tile_y, tower_type):
    if not (0 <= mouse_tile_x < c.COLS and 0 <= mouse_tile_y < c.ROWS):
        return False

    tile_num = mouse_tile_y * c.COLS + mouse_tile_x

    tower_rect = pg.Rect(
        mouse_tile_x * c.TILE_SIZE,
        mouse_tile_y * c.TILE_SIZE,
        c.TILE_SIZE,
        c.TILE_SIZE
    )

    #no tower zones
    for zone_rect in game_world.no_tower_zones:
        if tower_rect.colliderect(zone_rect):
            return False

    #cliff zones
    is_in_cliff_zone = any(
        tower_rect.colliderect(zone)
        for zone in game_world.cliff_tower_zones
    )

    if tower_type == "druid" and not is_in_cliff_zone:
        return False

    if tower_type in ("warrior", "cadence", "thief", "monk") and is_in_cliff_zone:
        return False

    #proximity check
    for tower in tower_group:
        same_zone_type = (
            (tower_type == "druid" and tower.tower_type == "druid") or
            (tower_type != "druid" and tower.tower_type != "druid")
        )

        if same_zone_type:
            dist_x = tower.tile_x - mouse_tile_x
            dist_y = tower.tile_y - mouse_tile_y

            if abs(dist_x) <= 0.5 and abs(dist_y) <= 0.5:
                return False

    #tile validity
    if game_world.tile_map[tile_num] == 0:
        return False

    #occupied check
    for tower in tower_group:
        if (mouse_tile_x, mouse_tile_y) == (tower.tile_x, tower.tile_y):
            return False

    return True

def create_tower(mouse_pos):
    mouse_tile_x = mouse_pos[0] // c.TILE_SIZE
    mouse_tile_y = mouse_pos[1] // c.TILE_SIZE

    if not (0 <= mouse_tile_x < c.COLS and 0 <= mouse_tile_y < c.ROWS):
        print("Clicked outside map bounds!")
        return

    if not can_place_tower(mouse_tile_x, mouse_tile_y, selected_tower_type):
        print("Invalid placement.")
        return

    if len(tower_group) >= c.GLOBAL_TOWER_LIMIT:
        print(f"Cannot place tower: reached global tower limit of {c.GLOBAL_TOWER_LIMIT}.")
        return

    druid_count = sum(1 for t in tower_group if t.tower_type == "druid")
    warrior_count = sum(1 for t in tower_group if t.tower_type == "warrior")
    cadence_count = sum(1 for t in tower_group if t.tower_type == "cadence")
    thief_count = sum(1 for t in tower_group if t.tower_type == "thief")
    monk_count = sum(1 for t in tower_group if t.tower_type == "monk")

    print(f"Number of towers before placement: {len(tower_group)}")

    #placement logic
    if selected_tower_type == "warrior":
        if warrior_count >= c.WARRIOR_MAX_COUNT:
            print(f"Cannot place more than {c.WARRIOR_MAX_COUNT} warrior towers.")
            return
        if game_world.silver >= c.WARRIOR_COST:
            new_tower = Tower(warrior_spritesheets, mouse_tile_x, mouse_tile_y, tower_type="warrior")
            tower_group.add(new_tower)
            game_world.tower_group.add(new_tower)
            game_world.silver -= c.WARRIOR_COST
            sound_cache.SOUND_CACHE["ui_rustle"].play()
        else:
            print("Not enough silver to place warrior tower.")

    elif selected_tower_type == "druid":
        if druid_count >= c.DRUID_MAX_COUNT:
            print(f"Cannot place more than {c.DRUID_MAX_COUNT} druid towers.")
            return
        if game_world.silver >= c.DRUID_COST:
            new_tower = Tower(druid_spritesheets, mouse_tile_x, mouse_tile_y, tower_type="druid")
            tower_group.add(new_tower)
            game_world.tower_group.add(new_tower)
            game_world.silver -= c.DRUID_COST
            sound_cache.SOUND_CACHE["ui_rustle"].play()
        else:
            print("Not enough silver to place druid tower.")

    elif selected_tower_type == "cadence":
        if cadence_count >= c.CADENCE_MAX_COUNT:
            print(f"Cannot place more than {c.CADENCE_MAX_COUNT} cadence towers.")
            return
        if game_world.silver >= c.CADENCE_COST:
            new_tower = Tower(cadence_spritesheets, mouse_tile_x, mouse_tile_y, tower_type="cadence")
            tower_group.add(new_tower)
            game_world.tower_group.add(new_tower)
            game_world.silver -= c.CADENCE_COST
            sound_cache.SOUND_CACHE["ui_rustle"].play()
        else:
            print("Not enough silver to place cadence tower.")

    elif selected_tower_type == "monk":
        if monk_count >= c.MONK_MAX_COUNT:
            print(f"Cannot place more than {c.MONK_MAX_COUNT} monk towers.")
            return
        if game_world.silver >= c.MONK_COST:
            new_tower = Tower(monk_spritesheets, mouse_tile_x, mouse_tile_y, tower_type="monk")
            tower_group.add(new_tower)
            game_world.tower_group.add(new_tower)
            game_world.silver -= c.MONK_COST
            sound_cache.SOUND_CACHE["ui_rustle"].play()
        else:
            print("Not enough silver to place monk tower.")

    elif selected_tower_type == "thief":
        if thief_count >= c.THIEF_MAX_COUNT:
            print(f"Cannot place more than {c.THIEF_MAX_COUNT} thief towers.")
            return
        if game_world.silver >= c.THIEF_COST:
            new_tower = Tower(thief_spritesheets, mouse_tile_x, mouse_tile_y, tower_type="thief")
            tower_group.add(new_tower)
            game_world.tower_group.add(new_tower)
            game_world.silver -= c.THIEF_COST
            sound_cache.SOUND_CACHE["ui_rustle"].play()
        else:
            print("Not enough silver to place thief tower.")

def select_tower(mouse_pos):
    mouse_tile_x = mouse_pos[0] // c.TILE_SIZE
    mouse_tile_y = mouse_pos[1] // c.TILE_SIZE
    for tower in tower_group:
        if (mouse_tile_x, mouse_tile_y) == (tower.tile_x, tower.tile_y):
            return tower


#create sprite groups
enemy_group = pg.sprite.Group()
tower_group = pg.sprite.Group()

#create buttons
warrior_button = Button(c.SCREEN_WIDTH + 30, 30, buy_warrior_image, True)
druid_button = Button(c.SCREEN_WIDTH + 125, 30, buy_druid_image, True)
cadence_button = Button(c.SCREEN_WIDTH + 220, 30, buy_cadence_image, True)
thief_button = Button(c.SCREEN_WIDTH + 30, 100, buy_thief_image, True)
dragonsage_button = Button(c.SCREEN_WIDTH + 125, 100, buy_dragonsage_image, True)
cancel_button = Button(c.SCREEN_WIDTH + 185, 180, cancel_button_image, True)
begin_button = Button(175, 380, begin_image, True)
restart_button = Button(310, 300, restart_image, True)
fast_forward_button = Button(460, 460, fast_forward_image, False)
button_was_pressed = False

if not game_over:
    pg.mixer.music.load("ambience.wav")
    pg.mixer.music.set_volume(0.2)
    pg.mixer.music.play(-1)

hovered_button = None

#game loop
run = True
while run:
    clock.tick(c.FPS)

    #########################
    # UPDATING SECTION
    #########################

    if not game_over:

        #check if player has lost
        if game_world.health <= 0:
            show_death_screen(screen)
            game_over = False
            level_started = False
            placing_towers = False
            selected_tower = None
            tower_panel.hide()

            #reset game world
            game_world = world.World(world_data, map_image, enemy_images, clock)
            game_world.process_data()
            game_world.process_enemies()

            pg.mixer.stop()
            game_world.enemy_group.empty()
            tower_group.empty()



        #check if player has won
        if game_world.level > c.TOTAL_LEVELS:
            game_over = True
            game_outcome = 1  #win

        #update towers
        tower_group.update(game_world.enemy_group, game_world)

        #reset buffs on all towers
        for tower in tower_group:
            tower.reset_buffs()

        #apply cadence buffs to other towers in range
        cadence_towers = [t for t in tower_group if t.tower_type == "cadence"]
        for cadence in cadence_towers:
            for tower in tower_group:
                if tower != cadence:
                    dist = math.hypot(
                        (cadence.tile_x - tower.tile_x) * c.TILE_SIZE,
                        (cadence.tile_y - tower.tile_y) * c.TILE_SIZE
                    )
                    if dist <= cadence.range:
                        tower.apply_buffs(cooldown_buff=cadence.speed_buff)

        #clear selection on all towers
        for tower in tower_group:
            tower.selected = False

        #highlight selected tower if any
        if selected_tower:
            selected_tower.selected = True
            tower_panel.show()
        else:
            tower_panel.hide()

    #########################
    # DRAWING SECTION
    #########################

    #draw level and enemies
    game_world.draw(screen)
    game_world.update_enemies()

    for enemy in enemy_group:
        enemy.draw(screen)

    #draw GUI and pillars
    display_data()
    screen.blit(pillar_foreground, (0, 0))

    #draw towers sorted by type priority
    for tower in sorted(tower_group, key=lambda t: 0 if t.tower_type == "warrior" else 1):
        tower.draw(screen)

    #draw lightning
    for effect in game_world.lightning_effects:
        effect.draw(screen)

    if not game_over:
        #check if the level has started
        if not level_started:
            if begin_button.draw(screen):
                level_started = True
                game_world.start_wave()
                sound_cache.SOUND_CACHE["begin-wave"].play()


        else:
            button_pressed = fast_forward_button.draw(screen)
            if button_pressed and not button_was_pressed:
                game_world.game_speed = 1 if game_world.game_speed == 2 else 2
            button_was_pressed = button_pressed
            if game_world.wave_active:
                current_time = pg.time.get_ticks()
                game_world.try_spawn_next_enemy(current_time)

        #check if wave is finished
        if game_world.check_level_complete():
            game_world.silver += game_world.level_reward
            game_world.level += 1
            game_world.reward_increment = min(game_world.reward_increment + 25, game_world.max_reward_increment)
            game_world.level_reward = min(game_world.level_reward + game_world.reward_increment,
                                          game_world.max_level_reward)
            level_started = False
            game_world.process_enemies()
            game_world.spawned_enemies = 0
            game_world.killed_enemies = 0
            game_world.missed_enemies = 0

        #tower placement buttons
        if warrior_button.draw(screen):
            placing_towers = True
            selected_tower_type = "warrior"
            sound_cache.SOUND_CACHE["tower-button-select"].play()
        if druid_button.draw(screen):
            placing_towers = True
            selected_tower_type = "druid"
            sound_cache.SOUND_CACHE["tower-button-select"].play()
        if cadence_button.draw(screen):
            placing_towers = True
            selected_tower_type = "cadence"
            sound_cache.SOUND_CACHE["tower-button-select"].play()
        if thief_button.draw(screen):
            placing_towers = True
            selected_tower_type = "thief"
            sound_cache.SOUND_CACHE["tower-button-select"].play()
        if dragonsage_button.draw(screen):
            placing_towers = True
            selected_tower_type = "monk"
            sound_cache.SOUND_CACHE["tower-button-select"].play()

        #hover tooltips code
        mouse_pos = pg.mouse.get_pos()

        new_hovered = None
        hover_text = ""

        if warrior_button.rect.collidepoint(mouse_pos):
            hover_text = f"Warrior - Cost: {c.WARRIOR_COST} - A front-line swordsman. Can upgrade into a Sigil Knight with elemental charges or a rune-collecting Wraith Knight. MAX: {c.WARRIOR_MAX_COUNT}"
            tooltip_x = warrior_button.rect.right + 10
            tooltip_y = warrior_button.rect.top + 55
            new_hovered = "warrior"

        elif druid_button.rect.collidepoint(mouse_pos):
            hover_text = f"Scholar - Cost: {c.DRUID_COST} - Cliff tower unit, deals heavy magic damage. Can become a slow-hitting Druid or a rapid-casting Illusionist. MAX: {c.DRUID_MAX_COUNT}"
            tooltip_x = druid_button.rect.right + 10
            tooltip_y = druid_button.rect.top + 55
            new_hovered = "druid"

        elif cadence_button.rect.collidepoint(mouse_pos):
            hover_text = f"Cadence - Cost: {c.CADENCE_COST} - Buff nearby towers with music, increasing their attack speed. MAX: {c.CADENCE_MAX_COUNT}"
            tooltip_x = cadence_button.rect.right + 10
            tooltip_y = cadence_button.rect.top + 55
            new_hovered = "cadence"

        elif thief_button.rect.collidepoint(mouse_pos):
            hover_text = f"Thief - Cost: {c.THIEF_COST} - A deadly assassin. Joining the Faceless Order unlocks the ability to chain attacks or strike single targets rapidly as a Shinobi. MAX: {c.THIEF_MAX_COUNT}"
            tooltip_x = thief_button.rect.right + 10
            tooltip_y = thief_button.rect.top + 55
            new_hovered = "thief"

        elif dragonsage_button.rect.collidepoint(mouse_pos):
            hover_text = f"Brawler - Cost: {c.MONK_COST} - A master of the fist. Can upgrade into a Dragon Sage to stun targets with lightning, or an Oni for pure raw striking power. MAX: {c.MONK_MAX_COUNT}"
            tooltip_x = dragonsage_button.rect.right + 10
            tooltip_y = dragonsage_button.rect.top + 55
            new_hovered = "dragonsage"

        if new_hovered != hovered_button and new_hovered is not None:
            sound_cache.SOUND_CACHE["ui_hover"].play()

        hovered_button = new_hovered

        if hover_text:
            font = pg.font.Font("../assets/fonts/HWYGOTH.TTF", font_size - 6)
            max_width = 270

            def wrap_text(text, font, max_width):
                words = text.split(' ')
                lines = []
                current_line = ""

                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    if font.size(test_line)[0] <= max_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                return lines


            lines = wrap_text(hover_text, font, max_width)

            padding = 5
            line_height = font.get_linesize()
            tooltip_height = line_height * len(lines)
            tooltip_width = max(font.size(line)[0] for line in lines)

            if tooltip_x + tooltip_width + 2 * padding > c.SCREEN_WIDTH + c.SIDE_PANEL:
                tooltip_x = c.SCREEN_WIDTH + c.SIDE_PANEL - tooltip_width - 2 * padding - 10
            if tooltip_y + tooltip_height + 2 * padding > c.SCREEN_HEIGHT:
                tooltip_y = c.SCREEN_HEIGHT - tooltip_height - 10
            if tooltip_y < 0:
                tooltip_y = 10

            #draw background and text
            pg.draw.rect(screen, "white", (tooltip_x, tooltip_y, tooltip_width + 2 * padding, tooltip_height + 2 * padding))
            pg.draw.rect(screen, "black", (tooltip_x, tooltip_y, tooltip_width + 2 * padding, tooltip_height + 2 * padding), 1)

            for i, line in enumerate(lines):
                text_surface = font.render(line, True, "black")
                screen.blit(text_surface, (tooltip_x + padding, tooltip_y + padding + i * line_height))

        #tower placement cursor and range circle
        if placing_towers:
            mouse_pos = pg.mouse.get_pos()

            if mouse_pos[0] <= c.SCREEN_WIDTH and mouse_pos[1] <= c.SCREEN_HEIGHT:

                #snap to tile
                mouse_tile_x = mouse_pos[0] // c.TILE_SIZE
                mouse_tile_y = mouse_pos[1] // c.TILE_SIZE

                target_x = mouse_tile_x * c.TILE_SIZE + c.TILE_SIZE // 2
                target_y = mouse_tile_y * c.TILE_SIZE + c.TILE_SIZE // 2

                if not snap_initialized:
                    smooth_x, smooth_y = target_x, target_y
                    snap_initialized = True

                #interpolation

                lerp_speed = 0.14

                smooth_x += (target_x - smooth_x) * lerp_speed
                smooth_y += (target_y - smooth_y) * lerp_speed

                #tower data
                if selected_tower_type == "warrior":
                    cursor_img = warrior_cursor_img
                    range_radius = WARRIOR_DATA["base"]["range"]
                elif selected_tower_type == "druid":
                    cursor_img = druid_cursor_img
                    range_radius = DRUID_DATA["base"]["range"]
                elif selected_tower_type == "cadence":
                    cursor_img = cadence_cursor_img
                    range_radius = CADENCE_DATA[0]["range"]
                elif selected_tower_type == "thief":
                    cursor_img = thief_cursor_img
                    range_radius = THIEF_DATA["base"]["range"]
                elif selected_tower_type == "monk":
                    cursor_img = monk_cursor_img
                    range_radius = MONK_DATA["base"]["range"]
                else:
                    cursor_img = None
                    range_radius = 0

                valid_placement = can_place_tower(
                    mouse_tile_x,
                    mouse_tile_y,
                    selected_tower_type
                )

                #tile highlight
                tile_color = (0, 255, 0, 80) if valid_placement else (255, 0, 0, 80)

                tile_surf = pg.Surface((c.TILE_SIZE, c.TILE_SIZE), pg.SRCALPHA)
                pg.draw.rect(
                    screen,
                    (0, 255, 0) if valid_placement else (255, 0, 0),
                    (mouse_tile_x * c.TILE_SIZE, mouse_tile_y * c.TILE_SIZE, c.TILE_SIZE, c.TILE_SIZE),
                    2
                )

                screen.blit(
                    tile_surf,
                    (mouse_tile_x * c.TILE_SIZE, mouse_tile_y * c.TILE_SIZE)
                )

                range_color = (255, 255, 255, 100) if valid_placement else (255, 0, 0, 150)

                if range_radius > 0:
                    circle_surf = pg.Surface((range_radius * 2, range_radius * 2), pg.SRCALPHA)
                    pg.draw.circle(circle_surf, range_color, (range_radius, range_radius), range_radius)
                    screen.blit(circle_surf, (int(smooth_x - range_radius), int(smooth_y - range_radius)))
                if cursor_img:
                    cursor_rect = cursor_img.get_rect(center=(int(smooth_x), int(smooth_y)))
                    screen.blit(cursor_img, cursor_rect)
                    screen.blit(cursor_img, cursor_rect)

            cancel_button.draw(screen)

        tower_panel.draw(screen, selected_tower, game_world.silver)

    else:
        #game over screen
        pg.draw.rect(screen, "dodgerblue", (200, 200, 400, 200), border_radius=30)
        if game_outcome == -1:
            draw_text("GAME OVER", large_font, "grey0", 310, 230)
        elif game_outcome == 1:
            draw_text("YOU WIN!", large_font, "grey0", 315, 230)
        if restart_button.draw(screen):
            game_over = False
            level_started = False
            placing_towers = False
            selected_tower = None
            tower_panel.hide()

            #reset game world
            game_world = world.World(world_data, map_image, enemy_images, clock)
            game_world.process_data()
            game_world.process_enemies()

            pg.mixer.stop()
            enemy_group.empty()
            tower_group.empty()

    #########################
    # EVENT HANDLING
    #########################

    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pg.mouse.get_pos()

            if warrior_button.rect.collidepoint(mouse_pos):
                placing_towers = True
                selected_tower_type = "warrior"
            elif druid_button.rect.collidepoint(mouse_pos):
                placing_towers = True
                selected_tower_type = "druid"
            elif cadence_button.rect.collidepoint(mouse_pos):
                placing_towers = True
                selected_tower_type = "cadence"
            elif thief_button.rect.collidepoint(mouse_pos):
                placing_towers = True
                selected_tower_type = "thief"
            elif dragonsage_button.rect.collidepoint(mouse_pos):
                placing_towers = True
                selected_tower_type = "monk"
            elif cancel_button.rect.collidepoint(mouse_pos):
                placing_towers = False
                selected_tower_type = None
                sound_cache.SOUND_CACHE["ui-cancel"].play()
            elif (tower_panel.upgrade_btn_rect_a and tower_panel.upgrade_btn_rect_a.collidepoint(mouse_pos)) or \
                 (tower_panel.upgrade_btn_rect_b and tower_panel.upgrade_btn_rect_b.collidepoint(mouse_pos)) or \
                 (tower_panel.sell_btn_rect and tower_panel.sell_btn_rect.collidepoint(mouse_pos)):
                def do_upgrade(t, cost):
                    t.upgrade()
                    game_world.silver -= cost
                    sound_cache.SOUND_CACHE["upgrade"].play()
                def do_choose_path(t, path, cost):
                    t.choose_path(path)
                    game_world.silver -= cost
                    sound_cache.SOUND_CACHE["upgrade"].play()
                def do_sell(t):
                    refund = int(t.total_spent * c.REFUND_PERCENTAGE)
                    game_world.silver += refund
                    tower_group.remove(t)
                    game_world.tower_group.remove(t)
                    t.kill()
                    sound_cache.SOUND_CACHE["ui_rustle"].play()
                tower_panel.handle_event(event, selected_tower, game_world.silver, do_upgrade, do_choose_path, do_sell)
                if tower_panel.sell_btn_rect and tower_panel.sell_btn_rect.collidepoint(mouse_pos):
                    selected_tower = None
            else:
                if mouse_pos[0] < c.SCREEN_WIDTH and mouse_pos[1] < c.SCREEN_HEIGHT:
                    if placing_towers:
                        create_tower(mouse_pos)

                    else:
                        new_selected_tower = select_tower(mouse_pos)
                        if new_selected_tower is None:
                            if selected_tower is not None:
                                sound_cache.SOUND_CACHE["tower-unit-deselect"].play()
                            selected_tower = None
                            tower_panel.hide()
                        else:
                            if new_selected_tower is not selected_tower:
                                sound_cache.SOUND_CACHE["tower-unit-select"].play()
                            selected_tower = new_selected_tower
                else:
                    if selected_tower is not None:
                        sound_cache.SOUND_CACHE["tower-unit-deselect"].play()
                    selected_tower = None
                    tower_panel.hide()

    pg.display.flip()

pg.quit()