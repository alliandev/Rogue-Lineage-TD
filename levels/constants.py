ROWS = 25
COLS = 25
TILE_SIZE = 20
SIDE_PANEL = 300
SCREEN_WIDTH = TILE_SIZE * COLS
SCREEN_HEIGHT = TILE_SIZE * ROWS
FPS = 60
HEALTH = 3
SILVER = 650
TOTAL_LEVELS = 20

#enemy constants
SPAWN_COOLDOWN = 800
MIN_SPAWN_DISTANCE = 50

#tower constants
ANIMATION_STEPS = 6
ANIMATION_DELAY = 80


WARRIOR_COST = 200
UPGRADE_WARRIOR_BASE_COST = 100
UPGRADE_GROWTH_FACTOR_WARRIOR = 2
WARRIOR_LEVELS = 4
WARRIOR_MAX_COUNT = 12

DRUID_COST = 500
UPGRADE_DRUID_BASE_COST = 250
UPGRADE_GROWTH_FACTOR_DRUID = 3
DRUID_LEVELS = 4
DRUID_MAX_COUNT = 4

CADENCE_COST = 700
UPGRADE_CADENCE_BASE_COST = 500
UPGRADE_GROWTH_FACTOR_CADENCE = 2
CADENCE_LEVELS = 3
CADENCE_MAX_COUNT = 1

THIEF_COST = 150
UPGRADE_THIEF_BASE_COST = 25
UPGRADE_GROWTH_FACTOR_THIEF = 6
THIEF_LEVELS = 4
THIEF_MAX_COUNT = 6

MONK_COST = 300
UPGRADE_MONK_BASE_COST = 150
UPGRADE_GROWTH_FACTOR_MONK = 2.5
MONK_LEVELS = 4
MONK_MAX_COUNT = 3

GLOBAL_TOWER_LIMIT = 36

DRAGON_SAGE_MARKS_REQUIRED = 5
DRAGON_SAGE_STUN_DURATION = 950
DRAGON_SAGE_STUN_COOLDOWN = 2000
DRAGON_SAGE_MARK_RESET_TIME = 3000

def get_warrior_upgrade_cost(base_cost, current_level, growth_factor=UPGRADE_GROWTH_FACTOR_WARRIOR):
    return int(base_cost * (growth_factor ** (current_level - 1)))

def get_druid_upgrade_cost(base_cost, current_level, growth_factor=UPGRADE_GROWTH_FACTOR_DRUID):
    return int(base_cost * (growth_factor ** (current_level - 1)))

def get_cadence_upgrade_cost(base_cost, current_level, growth_factor=UPGRADE_GROWTH_FACTOR_CADENCE):
    return int(base_cost * (growth_factor ** (current_level - 1)))

def get_thief_upgrade_cost(base_cost, current_level, growth_factor=UPGRADE_GROWTH_FACTOR_THIEF):
    return int(base_cost * (growth_factor ** (current_level - 1)))

def get_monk_upgrade_cost(base_cost, current_level, growth_factor=UPGRADE_GROWTH_FACTOR_MONK):
    return int(base_cost * (growth_factor ** (current_level - 1)))


KILL_REWARD = 10
LEVEL_COMPLETE_REWARD = 100
REFUND_PERCENTAGE = 0.70
