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
DIRECTIONS = {(0, -1): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3}

# The Isolist That holds all isometric items
ISO_LIST = IsoList()
"""
FUNCTIONS
"""


def clamp(value, low=0, high=1):
    return min(max(value, low), high)


def round_to_x(value, x):
    return round(value/x)*x


def iso_append(item):
    global ISO_LIST
    ISO_LIST.append(item)
    ISO_LIST.reorder_isometric()


def iso_extend(iterable):
    for item in iterable:
        iso_append(item)
    ISO_LIST.reorder_isometric()