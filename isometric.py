from dataclasses import dataclass
from math import *

import arcade

import constants as c
import turn


def cast_to_iso(e_x: float, e_y: float, z_mod=0, debug=False):
    """
    Casts the imputed Euclidean x and y co-ordinates to the equivalent isometric x, y, z co-ordinates

    :param e_x: The Euclidean X that is to be cast to Isometric.
    :param e_y: The Euclidean Y that is to be cast to Isometric.
    :param z_mod: A z_mod which is added to put the object above or below anything with the same e_x and e_y.
    :param debug: The test simply outputs the final outputs for debugging.
    :return: the isometric x, y, z found.
    """

    e_x -= c.CURRENT_MAP_SIZE[0]/2
    e_y -= c.CURRENT_MAP_SIZE[1]/2

    # because the sprites are already cast to the ~30 degrees for the isometric the only needed rotations is the
    # 45 degrees. However since cos and sin 45 are both 0.707 they are removed from the system as it simply makes
    # the cast smaller
    iso_x = (e_x - e_y) * ((c.TILE_WIDTH*c.SPRITE_SCALE)/2)
    iso_y = -(e_x + e_y) * ((c.TILE_HEIGHT*c.SPRITE_SCALE)/2)
    iso_z = e_x + e_y + z_mod

    # reorder the IsoList then return the calculated values.
    if debug:
        print(iso_x, iso_y, iso_z)
    return iso_x, iso_y, iso_z


def cast_from_iso(x, y):
    relative_x = x/(c.TILE_WIDTH*c.SPRITE_SCALE) - y/(c.TILE_HEIGHT*c.SPRITE_SCALE) + 1
    relative_y = -x/(c.TILE_WIDTH*c.SPRITE_SCALE) - y/(c.TILE_HEIGHT*c.SPRITE_SCALE) + 1

    map_width, map_height = c.CURRENT_MAP_SIZE

    relative_x += map_width / 2
    relative_y += map_height / 2

    return floor(relative_x), floor(relative_y)


@dataclass()
class IsoTexture:
    location: str = ""
    hidden: str = None
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
    def __init__(self, e_x, e_y, iso_data: dict):
        x, y, z = cast_to_iso(e_x, e_y)
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
        self.mod_z = iso_texture.mod_z

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

    def new_pos(self, e_x, e_y, debug=False):
        self.center_x, self.center_y, self.center_z = cast_to_iso(e_x, e_y, self.mod_z, debug)
        self.center_x += self.mod_x*c.SPRITE_SCALE
        self.center_y += self.mod_y*c.SPRITE_SCALE
        self.e_x = e_x
        self.e_y = e_y
        c.iso_changed()


class IsoActor(IsoSprite):

    def __init__(self, e_x, e_y, iso_data: dict):
        super().__init__(e_x, e_y, iso_data)
        self.action_handler = turn.ActionHandler(self)
        self.path_finding_grid = None
        self.path_finding_data = None

    def set_grid(self, path_grid_2d):
        self.path_finding_grid = path_grid_2d
        self.load_paths()

    def load_paths(self):
        if self.path_finding_grid is not None:
            import algorithms
            self.path_finding_data = algorithms.path_2d(self.path_finding_grid, (self.e_y, self.e_x))


class IsoList(arcade.SpriteList):
    """
    The IsoList is basically identical to a normal arcade.SpriteList however it has a simple function which is called
    to order sprites by their "z" value so objects go behind walls but can then go in front of them.
    """

    def __init__(self):
        super().__init__()
        self.changed = True

    def draw(self, **kwargs):
        if self.changed:
            self.reorder_isometric()
            self.changed = False
        super().draw(**kwargs)

    def append(self, item):
        super().append(item)
        self.changed = True

    def remove(self, item):
        super().remove(item)
        self.changed = True

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



