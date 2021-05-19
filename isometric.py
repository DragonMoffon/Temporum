from dataclasses import dataclass
from typing import Union
from pathlib import Path
from math import *

import arcade

import constants as c


@dataclass()
class IsoTexture:
    location: Union[str, Path] = ""
    hidden: Union[str, Path] = None
    mod_x: float = .0
    mod_y: float = .0
    mod_z: float = .0

    s_x: int = 0
    s_y: int = 0

    width: int = 0
    height: int = 0


class IsoSprite(arcade.Sprite):
    """
    The base isometric tile class, basically just the arcade.Sprite with methods and variables for isometric casting.
    """
    def __init__(self, e_x, e_y, x, y, z, iso_data: dict, z_mod=0):
        if isinstance(iso_data, dict):
            iso_texture: IsoTexture = iso_data['texture']
            directions = iso_data['directions']
        else:
            iso_texture: IsoTexture = iso_data
            directions = None
        super().__init__(iso_texture.location, c.SPRITE_SCALE,
                         iso_texture.s_x, iso_texture.s_y,
                         iso_texture.width, iso_texture.height)
        # The center positions of the tile.
        self.center_x = x + iso_texture.mod_x*c.SPRITE_SCALE
        self.center_y = y + iso_texture.mod_y*c.SPRITE_SCALE
        self.center_z = z + iso_texture.mod_z

        # the mod_x, and mod_y
        self.mod_x = iso_texture.mod_x
        self.mod_y = iso_texture.mod_y
        self.mod_z = z_mod + iso_texture.mod_z

        # The isometric data
        self.iso_texture = iso_texture
        self.direction = directions

        # The euclidean position of the sprite.
        self.e_x = e_x
        self.e_y = e_y

        # textures for functions
        self.base = self.texture
        if iso_texture.hidden is not None:
            self.hidden = arcade.load_texture(iso_texture.hidden, iso_texture.s_x, iso_texture.s_y,
                                              iso_texture.width, iso_texture.height)
        else:
            self.hidden = None

    def new_pos(self, e_x, e_y, map_size=None, debug=False):
        self.center_x, self.center_y, self.center_z = cast_to_iso(e_x, e_y, map_size, self.mod_z, debug)
        self.center_x += self.mod_x*c.SPRITE_SCALE
        self.center_y += self.mod_y*c.SPRITE_SCALE
        c.ISO_LIST.reorder_isometric()
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

    def __init__(self, layer_data, map_data, sprite_data, tile_map, shown=True):
        self.layer_data = layer_data
        self.map_data = map_data
        self.tiles = sprite_data
        self.tile_map = tile_map
        self.shown = shown


@dataclass()
class IsoRoom:
    room_walls: arcade.SpriteList
    shown: bool = True


def cast_to_iso(e_x, e_y, map_size=None, z_mod=0, debug=False):
    """
    Casts the imputed Euclidean x and y co-ordinates to the equivalent isometric x, y, z co-ordinates

    :param e_x: The Euclidean X that is to be cast to Isometric.
    :param e_y: The Euclidean Y that is to be cast to Isometric.
    :param map_size: A tuple of the width and height
    :param z_mod: A z_mod which is added to put the object above or below anything with the same e_x and e_y.
    :param debug: The test simply outputs the final outputs for debugging.
    :return: the isometric x, y, z found.
    """
    if map_size is not None:
        # Find the needed values
        map_width, map_height = map_size
    else:
        map_width = 20
        map_height = 20

    e_x -= map_width/2
    e_y -= map_height/2

    # because the sprites are already cast to the ~30 degrees for the isometric the only needed rotations is the
    # 45 degrees. However since cos and sin 45 are both 0.707 they are removed from the system as it simply makes
    # the cast smaller
    iso_x = (e_x - e_y) * ((c.TILE_WIDTH*c.SPRITE_SCALE)/2)
    iso_y = -(e_x + e_y) * ((c.TILE_HEIGHT*c.SPRITE_SCALE)/2)
    iso_z = e_x + e_y + z_mod

    # reorder the IsoList then return the calculated values.
    if c.ISO_LIST is not None:
        c.ISO_LIST.reorder_isometric()
    if debug:
        print(iso_x, iso_y, iso_z)
    return iso_x, iso_y, iso_z


def cast_from_iso(x, y, map_size):
    relative_x = x/(c.TILE_WIDTH*c.SPRITE_SCALE) - y/(c.TILE_HEIGHT*c.SPRITE_SCALE) + 1
    relative_y = -x/(c.TILE_WIDTH*c.SPRITE_SCALE) - y/(c.TILE_HEIGHT*c.SPRITE_SCALE) + 1

    map_width, map_height = map_size

    relative_x += map_width / 2
    relative_y += map_height / 2

    return floor(relative_x), floor(relative_y)
