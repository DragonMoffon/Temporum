from dataclasses import dataclass
from typing import Union
from pathlib import Path
from math import *

import arcade

import constants as c


@dataclass()
class IsoTexture:
    """
    location: str = ""
    mod_x: float = .0
    mod_y: float = .0

    s_x: int = 0
    s_y: int = 0

    width: int = 0
    height: int = 0
    """

    location: Union[str, Path] = ""
    mod_x: float = .0
    mod_y: float = .0

    s_x: int = 0
    s_y: int = 0

    width: int = 0
    height: int = 0


class IsoSprite(arcade.Sprite):
    """
    The base isometric tile class, basically just the arcade.Sprite with methods and variables for isometric casting.
    """
    def __init__(self, e_x, e_y, x, y, z, iso_data: IsoTexture):
        super().__init__(iso_data.location, c.SPRITE_SCALE,
                         iso_data.s_x, iso_data.s_y,
                         iso_data.width, iso_data.height)
        # The center positions of the tile.
        self.center_x = x + iso_data.mod_x*c.SPRITE_SCALE
        self.center_y = y + iso_data.mod_y*c.SPRITE_SCALE
        self.center_z = z

        # the mod_x, and mod_y
        self.mod_x = iso_data.mod_x
        self.mod_y = iso_data.mod_y

        # The euclidean position of the sprite.
        self.e_x = e_x
        self.e_y = e_y

    def new_pos(self, e_x, e_y, e_map, iso_list=None, z_mod=0, debug=False):
        self.center_x, self.center_y, self.center_z = cast_to_iso(e_x, e_y, e_map, None, z_mod, debug)
        iso_list.reorder_isometric()
        self.center_x += self.mod_x*c.SPRITE_SCALE
        self.center_y += self.mod_y*c.SPRITE_SCALE
        self.e_x = e_x
        self.e_y = e_y


class IsoList(arcade.SpriteList):
    """
    The IsoList is basically identical to a normal arcade.SpriteList however it has a simple function which is called
    to order sprites by their "z" value so objects go behind walls but can then go in front of them.
    """

    def reorder_isometric(self):
        """
        This orders the sprites by their z value and then sorts the sprites index's and destroy the Vertex Object so
        a new re-oredered vao is created at draw time.

        This does slow down the one draw frame it happens however, This is hopefully unnoticeable.
        """
        self.sprite_list = sorted(self.sprite_list, key=lambda tile: tile.center_z)

        for idx, sprite in enumerate(self.sprite_list):
            self.sprite_idx[sprite] = idx

        self._vao1 = None


class IsoLayer:

    def __init__(self, layer_data, map_data, sprite_data):
        self.layer_data = layer_data
        self.map_data = map_data
        self.tiles = sprite_data
        self.shown = True


def cast_to_iso(e_x, e_y, e_map, iso_list: IsoList = None, z_mod=0, debug=False):
    """
    Casts the imputed Euclidean x and y co-ordinates to the equivalent isometric x, y, z co-ordinates

    :param e_x: The Euclidean X that is to be cast to Isometric.
    :param e_y: The Euclidean Y that is to be cast to Isometric.
    :param e_map: The 2D array which the tile is in.
    :param iso_list: The IsoList the sprite which has the e_x, e_y.
    :param z_mod: A z_mod which is added to put the object above or below anything with the same e_x and e_y.
    :param debug: The test simply outputs the final outputs for debugging.
    :return: the isometric x, y, z found.
    """
    # Find the needed values
    map_width, map_height = len(e_map), len(e_map[0])

    # because the sprites are already cast to the ~30 degrees for the isometric the only needed rotations is the
    # 45 degrees. However since cos and sin 45 are both 0.707 they are removed from the system as it simply makes
    # the cast smaller
    iso_x = (e_x - e_y) * (c.TILE_WIDTH*c.SPRITE_SCALE)/2
    iso_y = (e_x + e_y) * (c.TILE_HEIGHT*c.SPRITE_SCALE)/2
    iso_z = (map_width - e_x) + (map_height - e_y) + z_mod

    # reorder the IsoList then return the calculated values.
    if iso_list is not None:
        iso_list.reorder_isometric()
    if debug:
        print(iso_x, iso_y, iso_z)
    return iso_x, iso_y, iso_z


def cast_from_iso(x, y, e_map):
    relative_x = x/(c.TILE_WIDTH*c.SPRITE_SCALE) + y/(c.TILE_HEIGHT*c.SPRITE_SCALE)
    relative_y = ((2*y)/(c.TILE_HEIGHT*c.SPRITE_SCALE)) - relative_x

    map_width, map_height = len(e_map), len(e_map[0])

    return floor(relative_x), floor(relative_y)
