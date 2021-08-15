from dataclasses import dataclass
from math import *

import arcade

import constants as c
from turn import ActionHandler
import tiles


def cast_to_iso(e_x: float, e_y: float, mods: tuple = (0, 0, 0)):
    """
    Casts the inputted Euclidean x and y co-ordinates to the equivalent isometric x, y, w co-ordinates

    :param e_x: The Euclidean X that is to be cast to Isometric.
    :param e_y: The Euclidean Y that is to be cast to Isometric.
    :param mods: A tuple of 3 floats that are the x, y, and w mods.
    :return: the isometric x, y, w found.
    """

    e_x -= c.CURRENT_MAP_SIZE[0]/2
    e_y -= c.CURRENT_MAP_SIZE[1]/2

    # because the sprites are already cast to the ~30 degrees for the isometric the only needed rotations is the
    # 45 degrees. However since cos and sin 45 are both 0.707 they are removed from the system as it simply makes
    # the cast smaller
    iso_x = (e_x - e_y) * ((c.TILE_WIDTH*c.SPRITE_SCALE)/2) + mods[0]*c.SPRITE_SCALE
    iso_y = -(e_x + e_y) * ((c.TILE_HEIGHT*c.SPRITE_SCALE)/2) + mods[1]*c.SPRITE_SCALE
    iso_w = e_x + e_y + mods[2]

    # return the calculated values.
    return iso_x, iso_y, iso_w


def cast_from_iso(x, y):
    relative_x = x/(c.TILE_WIDTH*c.SPRITE_SCALE) - y/(c.TILE_HEIGHT*c.SPRITE_SCALE) + 1
    relative_y = -x/(c.TILE_WIDTH*c.SPRITE_SCALE) - y/(c.TILE_HEIGHT*c.SPRITE_SCALE) + 1

    map_width, map_height = c.CURRENT_MAP_SIZE

    relative_x += map_width / 2
    relative_y += map_height / 2

    return floor(relative_x), floor(relative_y)


@dataclass()
class IsoData:
    texture: arcade.Texture
    hidden: arcade.Texture
    relative_pos: tuple = (0, 0)
    position_mods: tuple = (0, 0, 0)
    directions: tuple = (0, 0, 0, 0)
    vision: tuple = (0, 0, 0, 0)
    actions: tuple = ()


class IsoAnimation:

    def __init__(self, location, size, start_xy, frames, speed):
        self.current_frame = 0
        self.frame_timer = 0
        self.animation_speed = speed
        self.textures = []
        self.frames = 0
        self.frame = 0
        y = start_xy[1]
        x = start_xy[0]
        while frames > self.frames:
            try:
                texture = arcade.load_texture(location, x, y, *size)
                self.textures.append(texture)
                self.frames += 1
                x += size[0]
            except ValueError:
                x = start_xy[0]
                y += size[1]

                if y >= 10*size[1]:
                    print("animation error. The number of frames, or the size is incorrect.")
                    break

    def update_animation(self, delta_time):
        self.frame_timer += delta_time
        if self.frame_timer > self.animation_speed:
            self.frame_timer -= self.animation_speed
            self.frame += 1
            if self.frame >= self.frames:
                self.frame = 0
                return None

        return self.textures[self.frame]


class IsoSprite(arcade.Sprite):
    """
    The base isometric tile class, basically just the arcade.Sprite with methods and variables for isometric casting.
    """
    def __init__(self, e_x, e_y, tile_data: IsoData):
        self.relative_pos = tile_data.relative_pos
        self.position_mods = tile_data.position_mods
        x, y, w = cast_to_iso(e_x + self.relative_pos[0], e_y + self.relative_pos[1])
        super().__init__(scale=c.SPRITE_SCALE)
        # The center positions of the tile.
        self.center_x = x + self.position_mods[0]*c.SPRITE_SCALE
        self.center_y = y + self.position_mods[1]*c.SPRITE_SCALE
        self.center_w = w + self.position_mods[2]

        # The isometric data
        self.tile_data = tile_data
        self.direction = tile_data.directions
        self.vision_direction = tile_data.vision
        self.actions = tile_data.actions

        # The euclidean position of the sprite.
        self.e_x = e_x + self.relative_pos[0]
        self.e_y = e_y + self.relative_pos[1]

        # textures for functions
        self.texture = tile_data.texture
        self.hidden = tile_data.hidden
        self.hide = False
        self.base = self.texture

        # tile for data retrieval and triggers
        self.tile = None

    def new_pos(self, e_x, e_y):
        self.center_x, self.center_y, self.center_w = cast_to_iso(e_x, e_y, self.position_mods)
        self.e_x = e_x + self.relative_pos[0]
        self.e_y = e_y + self.relative_pos[1]
        c.iso_changed()

    def set_iso_texture(self, tile_data: IsoData):
        self.relative_pos = tile_data.relative_pos
        self.position_mods = tile_data.position_mods
        x, y, w = cast_to_iso(self.e_x, self.e_y)

        # The center positions of the tile.
        self.center_x = x + self.position_mods[0] * c.SPRITE_SCALE
        self.center_y = y + self.position_mods[1] * c.SPRITE_SCALE
        self.center_w = w + self.position_mods[2]

        # The isometric data
        self.tile_data = tile_data
        self.direction = tile_data.directions
        self.vision_direction = tile_data.vision
        self.actions = tile_data.actions

        # textures for functions
        self.texture = tile_data.texture
        self.hidden = tile_data.hidden
        self.base = self.texture
        if self.hide:
            self.texture = self.hidden

        if self.tile is not None:
            self.tile.update(self)


class IsoActor(IsoSprite):

    def __init__(self, e_x, e_y, tile_data: IsoData, initiative=10):
        super().__init__(e_x, e_y, tile_data)
        self.action_handler = ActionHandler(self, initiative)
        self.algorithm = "base"
        self.path_finding_grid = None
        self.path_finding_data = None

    def set_grid(self, path_grid_2d):
        self.path_finding_grid = path_grid_2d
        self.load_paths()

    def new_pos(self, e_x, e_y):
        if self.path_finding_grid is not None:
            old = self.path_finding_grid[self.e_x, self.e_y]
            if old is not None:
                old.light_remove(self)
            super().new_pos(e_x, e_y)
            new = self.path_finding_grid[e_x, e_y]
            if new is not None:
                new.light_add(self)
        else:
            super().new_pos(e_x, e_y)

    def new_map_pos(self, e_x, e_y):
        super().new_pos(e_x, e_y)
        new = self.path_finding_grid[e_x, e_y]
        if new is not None:
            new.light_add(self)

    def load_paths(self):
        if self.path_finding_grid is not None:
            from algorithms import path_2d
            self.path_finding_data = path_2d(self.path_finding_grid, (self.e_x, self.e_y),
                                             max_dist=self.action_handler.initiative,
                                             algorithm=self.algorithm)


class IsoInteractor(IsoSprite):

    def __init__(self, e_x, e_y, tile_data, interaction_data):
        super().__init__(e_x, e_y, tile_data)
        # The Node based conversation tree the IsoSprite needs
        self.interaction_data = interaction_data


class IsoStateSprite(IsoSprite):

    def __init__(self, e_x, e_y, tile_states, target_id):
        super().__init__(e_x, e_y, tile_states[0])
        self.states = tile_states
        self.current_state = 0
        self.id = target_id

    def toggle_states(self):
        self.current_state = (self.current_state + 1) % len(self.states)
        self.set_iso_texture(self.states[self.current_state])


class IsoGateSprite(IsoSprite):

    def __init__(self, e_x, e_y, iso_data, gate_data):
        super().__init__(e_x, e_y, iso_data)
        self.gate_data = gate_data


class IsoList(arcade.SpriteList):
    """
    The IsoList is basically identical to a normal arcade.SpriteList however it has a simple function which is called
    to order sprites by their "w" value so objects go behind walls but can then go in front of them.
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
        a new re-ordered vao is created at draw time.

        This does slow down the one draw frame it happens however, This is hopefully unnoticeable.
        """
        self.sprite_list = sorted(self.sprite_list, key=lambda tile: tile.center_w)

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


def find_poi_sprites(tile_id, node, pos_data):
    tile_data = tiles.find_iso_data(tile_id)
    pieces = []
    for piece in tile_data.pieces:
        data = IsoData(piece.texture, piece.hidden, piece.relative_pos,
                       (tile_data.pos_mods[0], tile_data.pos_mods[1], tile_data.pos_mods[2] + piece.mod_w),
                       tile_data.directions, tile_data.vision, tile_data.actions)
        pieces.append(IsoInteractor(*pos_data, data, node))

    return pieces


def find_toggle_sprites(tile_ids, target_id, pos_data):
    tile_data = [tiles.find_iso_data(i) for i in tile_ids]
    pieces = []
    for tile in tile_data:
        for piece in tile.pieces:
            data = IsoData(piece.texture, piece.hidden, piece.relative_pos,
                           (tile.pos_mods[0], tile.pos_mods[1], tile.pos_mods[2] + piece.mod_w),
                           tile.directions, tile.vision, tile.actions)
            pieces.append(data)
    return IsoStateSprite(*pos_data, pieces, target_id)


def find_iso_sprites(tile_id, pos_data):
    tile_data = tiles.find_iso_data(tile_id)
    pieces = []
    for piece in tile_data.pieces:
        data = IsoData(piece.texture, piece.hidden, piece.relative_pos,
                       (tile_data.pos_mods[0], tile_data.pos_mods[1], tile_data.pos_mods[2] + piece.mod_w),
                       tile_data.directions, tile_data.vision, tile_data.actions)
        pieces.append(IsoSprite(*pos_data, data))

    return pieces


def generate_iso_data_other(key):
    tile_data = tiles.OTHER_TEXTURES[key]
    pieces = []
    for piece in tile_data.pieces:
        data = IsoData(piece.texture, piece.hidden, piece.relative_pos,
                       (tile_data.pos_mods[0], tile_data.pos_mods[1], tile_data.pos_mods[2] + piece.mod_w),
                       tile_data.directions, tile_data.vision, tile_data.actions)
        pieces.append(data)

    return pieces
