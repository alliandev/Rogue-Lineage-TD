import pygame as pg

pg.mixer.init()

SOUND_CACHE = {
    "warrior_attack": pg.mixer.Sound("../assets/audio/warrior_attack.wav"),
    "druid_attack_1": pg.mixer.Sound("../assets/audio/druid_attack.wav"),
    "druid_attack_2": pg.mixer.Sound("../assets/audio/druid_attack-2.wav"),
    "cadence_song_1": pg.mixer.Sound("../assets/audio/cadence_song-1.wav"),
    "cadence_song_2": pg.mixer.Sound("../assets/audio/cadence_song-2.wav"),
    "cadence_song_3": pg.mixer.Sound("../assets/audio/cadence_song-3.wav"),
    "thief_attack_1": pg.mixer.Sound("../assets/audio/thief_attack-1.wav"),
    "thief_attack_2": pg.mixer.Sound("../assets/audio/thief_attack-2.wav"),
    "chain_lethality": pg.mixer.Sound("../assets/audio/chain_lethality.wav"),
    "monk_attack_1": pg.mixer.Sound("../assets/audio/monk-1.wav"),
    "monk_attack_2": pg.mixer.Sound("../assets/audio/monk-2.wav"),
    "monk_attack_3": pg.mixer.Sound("../assets/audio/monk-3.wav"),
    "monk_attack_4": pg.mixer.Sound("../assets/audio/monk-4.wav"),
    "hit_sound": pg.mixer.Sound("../assets/audio/oof.wav"),
    "death_sound": pg.mixer.Sound("../assets/audio/wipe.wav"),
    "necro_spawn": pg.mixer.Sound("../assets/audio/necro_spawn.wav"),
    "furantur": pg.mixer.Sound("../assets/audio/furantur.mp3"),
    "furantur_cast_sound": pg.mixer.Sound("../assets/audio/furantur-1.mp3"),
    "ui_hover": pg.mixer.Sound("../assets/audio/ui-hover.mp3"),
    "ui_rustle": pg.mixer.Sound("../assets/audio/ui-rustle.wav"),
    "confirm": pg.mixer.Sound("../assets/audio/confirm.mp3"),
    "upgrade": pg.mixer.Sound("../assets/audio/upgrade.wav"),
    "tower-button-select": pg.mixer.Sound("../assets/audio/tower-button-select.wav"),
    "tower-unit-select": pg.mixer.Sound("../assets/audio/tower-unit-select.mp3"),
    "tower-unit-deselect": pg.mixer.Sound("../assets/audio/tower-unit-deselect.mp3"),
    "ui-cancel": pg.mixer.Sound("../assets/audio/ui-cancel.wav"),
    "begin-wave": pg.mixer.Sound("../assets/audio/begin-wave.wav"),
    "monk-stun": pg.mixer.Sound("../assets/audio/monk-stun.wav"),
    "spin-kick": pg.mixer.Sound("../assets/audio/spin_kick.mp3"),
    "soul-rip": pg.mixer.Sound("../assets/audio/soul-rip.mp3")
}

mute_music = False
mute_sfx = False

_cadence_sound_channels = []

def set_mute_music(value: bool):
    global mute_music
    mute_music = value
    if mute_music:
        pg.mixer.music.set_volume(0.0)
    else:
        pg.mixer.music.set_volume(0.6)

    for ch in _cadence_sound_channels:
        if ch:
            ch.set_volume(0.0 if mute_music else 0.4)

def set_mute_sfx(value: bool):
    global mute_sfx
    mute_sfx = value
    for key, sound in SOUND_CACHE.items():
        if not key.startswith("cadence_song"):
            sound.set_volume(0.0 if mute_sfx else 0.6)

def register_cadence_channel(channel):
    if channel:
        _cadence_sound_channels.append(channel)

def stop_all_cadence_channels():
    global _cadence_sound_channels
    for ch in _cadence_sound_channels:
        if ch:
            ch.stop()
    _cadence_sound_channels.clear()
