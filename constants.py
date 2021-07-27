
import arcade

from isometric import IsoList


"""
VARIABLES
"""

# Isometric Sprite Data
TILE_WIDTH, TILE_HEIGHT = 160, 80
SPRITE_SCALE = 0.6
FLOOR_TILE_THICKNESS = 20

# Window Information
SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()

WINDOW_NAME, FULLSCREEN = "Temporum: The Melclex Incident", True

# Movement dictionary
DIRECTIONS = {(0, 1): 0, (1, 0): 1, (0, -1): 2, (-1, 0): 3}

# The Isolist That holds all isometric items
ISO_LIST = IsoList()
GROUND_LIST = IsoList()

# A list of walls for line of sight
WALLS = []

# The Player Object
PLAYER = None

# Map Information
CURRENT_MAP_SIZE = 0, 0


"""
FUNCTIONS
"""


def flush_walls():
    global WALLS
    WALLS = []


def add_wall(wall):
    global WALLS
    if wall not in WALLS:
        WALLS.append(wall)


def remove_wall(wall):
    global WALLS
    if wall in WALLS:
        WALLS.remove(wall)


def set_player(player):
    global PLAYER
    PLAYER = player


def set_map_size(size):
    global CURRENT_MAP_SIZE
    CURRENT_MAP_SIZE = tuple(size)


def clamp(value, low=0, high=1):
    return min(max(value, low), high)


def round_to_x(value, x):
    return round(value/x)*x


def iso_append(item):
    ISO_LIST.append(item)


def iso_extend(iterable: iter):
    for item in iterable:
        if item not in ISO_LIST:
            iso_append(item)


def iso_strip(iterable: iter):
    for item in iterable:
        if item in ISO_LIST:
            ISO_LIST.remove(item)


def iso_hide(iterable: iter):
    strips = []
    for item in iterable:
        if item.hidden is not None and item in ISO_LIST:
            item.texture = item.hidden
            item.hide = True
        else:
            strips.append(item)
    iso_strip(strips)


def iso_show(iterable: iter):
    show = []
    for item in iterable:
        item.texture = item.base
        item.hide = False
        if item not in ISO_LIST:
            show.append(item)
    iso_extend(show)


def iso_changed():
    ISO_LIST.changed = True


def set_floor(items):
    global GROUND_LIST
    GROUND_LIST = IsoList()
    GROUND_LIST.extend(items)
    GROUND_LIST.reorder_isometric()
