import arcade

import isometric
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

WINDOW_NAME, FULL_SCREEN = "Temporum: The Melclex Incident", True

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


def restart():
    """
    Resets all the constants.
    """
    global ISO_LIST
    ISO_LIST = isometric.IsoList()
    global GROUND_LIST
    GROUND_LIST = isometric.IsoList()
    set_player(None)
    set_map_size([0, 0])
    stop_music()


def set_player(player):
    """
    Set the player
    :param player: the player object
    """
    global PLAYER
    PLAYER = player


def set_map_size(size):
    """
    set map size
    :param size: a tuple/list of type (int, int)
    """
    global CURRENT_MAP_SIZE
    CURRENT_MAP_SIZE = tuple(size)


def clamp(value, low=0, high=1):
    """
    clamp value
    :param value: value
    :param low: lowest possible value
    :param high: highest possible value
    :return: the clamped value
    """
    return min(max(value, low), high)


def round_to_x(value, x):
    """
    round value to the nearest multiple of x

    if you have 16 and round to 5 it will return 15.

    :param value: the value to round
    :param x: the number to round to.
    :return: the rounded value
    """
    return int(round(value/x)*x)


def floor_to_x(value, x):
    """
    round value to the next lowest multiple of x.

    if you have 19 and floor to 5 it will return 15

    :param value: value to round
    :param x: the number to floor to
    :return: the floored value
    """
    return int(value/x)*x


def iso_append(item):
    """
    Add an iso sprite to the iso list.

    Will not add an item more than once, and will not add an item that is in the ground list.
    :param item: an iso sprite.
    """
    if item not in GROUND_LIST and item not in ISO_LIST:
        ISO_LIST.append(item)


def iso_extend(iterable: iter):
    """
    appends all items in the inputted iterable to the iso list.
    :param iterable: a iterable of iso sprites.
    """
    for item in iterable:
        iso_append(item)


def iso_strip(iterable: iter):
    """
    removes all items in inputted iterable from iso list
    :param iterable: an iterable of iso sprites
    """
    for item in iterable:
        ISO_LIST.remove(item)


def iso_remove(item):
    """
    removes the inputted iso sprite from the iso list

    only works if the item is in the iso list.
    :param item: an iso sprite
    """
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


def iso_changed():
    # If the iso list has changed or an item in the list has changed it's W value. then tell the program to resort
    # the iso list when the draw function is called.
    ISO_LIST.changed = True


def set_floor(items):
    # set the floor tiles.
    global GROUND_LIST
    GROUND_LIST = IsoList()
    GROUND_LIST.extend(items)
    GROUND_LIST.reorder_isometric()


"""
AUDIO FUNCTIONS
"""

# The base music and music player.
BASE_MUSIC = arcade.load_sound("audio/The Workshop 44100Hz Mono 16 bit.wav")
MUSIC_PLAYER = None


def start_music():
    # starts the music.
    global MUSIC_PLAYER
    if MUSIC_PLAYER is None:
        MUSIC_PLAYER = BASE_MUSIC.play(volume=0.15, pan=0.0, loop=True)


def stop_music():
    # stops the music
    global MUSIC_PLAYER
    if MUSIC_PLAYER is not None:
        BASE_MUSIC.stop(MUSIC_PLAYER)
        MUSIC_PLAYER = None
