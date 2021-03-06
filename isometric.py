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
        """
        An iso animation is just a class that holds the sprites and data for an aniamtion. By having it in it's own
        class it can be used to store pending animations.
        :param location: the image location
        :param size: a tuple of the images width and height
        :param start_xy: a tuple of the animations start x and y in the input image
        :param frames: the number of frames
        :param speed: the frames per second
        """
        self.current_frame = 0
        self.frame_timer = 0
        self.animation_speed = speed
        self.textures = []
        self.frames = 0
        self.frame = 0
        self.facing = 0
        y = start_xy[1]
        x = start_xy[0]

        # load the frames
        while frames > self.frames:
            try:
                # try and load a texture. If an error is generated that means we have moved too far on the x or y
                texture = arcade.load_texture(location, x, y, *size)
                flip_texture = arcade.load_texture(location, x, y, *size, flipped_horizontally=True)
                self.textures.append((texture, flip_texture))
                self.frames += 1
                x += size[0]
            except ValueError:
                # Since the x is to high lets reset and move down on the y.
                # if it complains multiple times then it's going to far on the y.
                x = 0
                y += size[1]

                if y >= 10*size[1]:
                    print("animation error. The number of frames, or the size is incorrect.")
                    break

    def start_animation(self):
        # start the animation by returning the first texture. SO there isn't a pause before the animation starts.
        return self.textures[self.frame][self.facing]

    def update_animation(self, delta_time):
        # increase the frame timer. If the timer goes above the FPS value then go to next frame.
        # if we go past our number of frames then return none to tell the animating sprite the animation is done
        self.frame_timer += delta_time
        if self.frame_timer > self.animation_speed:
            self.frame_timer -= self.animation_speed
            self.frame += 1
            if self.frame >= self.frames:
                self.frame = 0
                return None

        return self.textures[self.frame][self.facing]


class IsoSprite(arcade.Sprite):
    """
    The base isometric tile class, basically just the arcade.Sprite with methods and variables for isometric casting.
    """
    def __init__(self, e_x, e_y, tile_data: IsoData, animations=None):
        """
        the base of all isometric sprites. It stores alot more information than the standard sprite including a W
        values and more.
        :param e_x: the euclidean x pos
        :param e_y: the euclidean y pos
        :param tile_data: the tile data
        :param animations: any iso animations this sprite may have.
        """
        if animations is None:
            animations = {}
        # If the sprite is a piece of a larger item. then we need to find the relative position and mods.
        self.relative_pos = tile_data.relative_pos
        self.position_mods = tile_data.position_mods

        # Find the iso x, iso t and W value based on the e_x and e_y.
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

        # The animation system in the sprite.
        self.animations = animations
        self.pending_animations = []
        self.current_animation = None
        self.current_trigger = None

    def new_pos(self, e_x, e_y):
        # given a euclidean x and y find the new iso positions.
        self.center_x, self.center_y, self.center_w = cast_to_iso(e_x, e_y, self.position_mods)
        self.e_x = e_x + self.relative_pos[0]
        self.e_y = e_y + self.relative_pos[1]
        c.iso_changed()

    def set_iso_texture(self, tile_data: IsoData):
        # set the iso texture based on new tile data.
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

    def add_animation(self, animation, trigger, facing=0):
        # add a pending animation to the end of the list.
        if animation in self.animations:
            self.pending_animations.append((animation, trigger, facing))
        elif trigger is not None:
            trigger.done_animating()

    def push_animation(self, animation, trigger, facing=0):
        # add a pending animation to the front of the list.
        if animation in self.animations:
            self.pending_animations.insert(0, (animation, trigger, facing))
        elif trigger is not None:
            trigger.done_animating()

    def update_animation(self, delta_time: float = 1/60):
        """
        Every update this runs. The basic system is that every update it either animates or finds the next animation.
        :param delta_time: the difference between two frames in seconds. used to count how long an animation needs to
        run for.
        """

        if self.current_animation is not None:
            # If there is a current animation find the next frame.
            next_frame = self.current_animation.update_animation(delta_time)

            # if the animation is finished then the frame is none, else its the next texture needed.
            if next_frame is not None:
                self.texture = next_frame
            else:
                # If the animation was triggered by something we need to tell the trigger that it is done.
                if self.current_trigger is not None:
                    self.current_trigger.done_animating()
                    self.current_trigger = None

                # reset
                self.texture = self.base
                self.current_animation = None

                # if there are pending animations we want to start animating them.
                if len(self.pending_animations):
                    # Loop until we find the next valid animation. This is to protect against using the wrong key in a
                    # dict. Most of the time it will run once.
                    while len(self.pending_animations) and self.current_animation is None:
                        next_animation, next_trigger, facing = self.pending_animations.pop(0)
                        if next_animation in self.animations:
                            self.current_animation = self.animations[next_animation]
                            self.current_animation.facing = facing
                            self.current_trigger = next_trigger
                            self.texture = self.current_animation.start_animation()
                        else:
                            next_animation.done_animating()

        elif len(self.pending_animations):
            # Loop until we find the next valid animation. This is to protect against using the wrong key in a
            # dict. Most of the time it will run once.
            while len(self.pending_animations) and self.current_animation is None:
                next_animation, next_trigger, facing = self.pending_animations.pop(0)
                if next_animation in self.animations:
                    self.current_animation = self.animations[next_animation]
                    self.current_animation.facing = facing
                    self.current_trigger = next_trigger
                    self.texture = self.current_animation.start_animation()
                else:
                    next_animation.done_animating()


class IsoActor(IsoSprite):

    def __init__(self, e_x, e_y, tile_data: IsoData, initiative=10):
        """
        Same as an iso sprite but it also stores information needed about turn handling as this sprite is a turn actor.
        :param e_x: euclidean x pos
        :param e_y: euclidean y pos
        :param tile_data: tile data
        :param initiative: the base initative of the sprite
        """
        super().__init__(e_x, e_y, tile_data)
        self.action_handler = ActionHandler(self, initiative)
        self.algorithm = "base"
        self.path_finding_grid = None
        self.path_finding_data = None

    def set_grid(self, path_grid_2d):
        """
        Set the 2d grid array of tiles for pathfinding/
        :param path_grid_2d: the 2d array of tiles
        """
        self.path_finding_grid = path_grid_2d

    def new_pos(self, e_x, e_y):
        """
        Set the pos of the sprite based on the euclidean input pos, and change which tile the character can be found in.
        :param e_x:
        :param e_y:
        :return:
        """
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
        """
        this is the same as new pos but is for when a new map in being generated.
        :param e_x: euclidean x pos
        :param e_y: euclidean y pos
        """
        super().new_pos(e_x, e_y)
        new = self.path_finding_grid[e_x, e_y]
        if new is not None:
            new.light_add(self)

    def load_paths(self):
        """
        using the path finding grid. generate all the data needed for pathfinding.
        """
        if self.path_finding_grid is not None:
            from algorithms import path_2d
            self.path_finding_data = path_2d(self.path_finding_grid, (self.e_x, self.e_y),
                                             max_dist=self.action_handler.initiative,
                                             algorithm=self.algorithm)

    def hit(self, shooter):
        """
        If an iso actor is hit by anything.
        :param shooter: another iso actor.
        """
        print(self, "hit by", shooter)


class IsoInteractor(IsoSprite):

    def __init__(self, e_x, e_y, tile_data, interaction_data):
        """
        an Iso Sprite used for POI
        :param e_x: euclidean x pos
        :param e_y: euclidean y pos
        :param tile_data: the tile data
        :param interaction_data: the conversation node
        """
        super().__init__(e_x, e_y, tile_data)
        self.interaction_data = interaction_data


class IsoStateSprite(IsoSprite):

    def __init__(self, e_x, e_y, tile_states, target_id):
        """
        An Iso Sprite that has a bunch of different states that it can toggle through. used for doors.
        :param e_x: euclidean x pos
        :param e_y: euclidean y pos
        :param tile_states: the different states
        :param target_id: the id of the tile.
        """
        super().__init__(e_x, e_y, tile_states[0])
        self.states = tile_states
        self.current_state = 0
        self.id = target_id

    def toggle_states(self):
        self.current_state = (self.current_state + 1) % len(self.states)
        self.set_iso_texture(self.states[self.current_state])


class IsoGateSprite(IsoSprite):
    """
    an iso sprite that also has data for going to another room
    """
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
        """
        nigh pointless class that's here for backwards compatability.
        :param layer_data: the layer tmx
        :param map_data: a 2d array of numbers pointing to different spirtes.
        :param sprite_data: all the iso sprites
        :param tile_map: a 2d array of sprites
        :param shown: whether to show the layer or not.
        """
        self.layer_data = layer_data
        self.map_data = map_data
        self.tiles = sprite_data
        self.tile_map = tile_map
        self.shown = shown


def find_poi_sprites(tile_id, node, pos_data):
    """
    generate the Isodata for a POI iso sprite.
    :param tile_id: the target id to find the iso data.
    :param node: the node of the conversation tree
    :param pos_data: the position data
    :return: the iso interactor.
    """
    tile_data = tiles.find_iso_data(tile_id)
    pieces = []
    for piece in tile_data.pieces:
        data = IsoData(piece.texture, piece.hidden, piece.relative_pos,
                       (tile_data.pos_mods[0], tile_data.pos_mods[1], tile_data.pos_mods[2] + piece.mod_w),
                       tile_data.directions, tile_data.vision, tile_data.actions)
        pieces.append(IsoInteractor(*pos_data, data, node))

    return pieces


def find_toggle_sprites(tile_ids, target_id, pos_data):
    """
    find the iso data for toggle sprite.
    :param tile_ids: the ids of all the sprites
    :param target_id: the target id of the toggle sprite
    :param pos_data: the pos data
    :return: the IsoStateSprite
    """
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
    """
    Create Iso sprites from inputed tile id.
    :param tile_id: tile id.
    :param pos_data: position data
    :return: all the sprites that make up the tile id.
    """
    tile_data = tiles.find_iso_data(tile_id)
    pieces = []
    for piece in tile_data.pieces:
        data = IsoData(piece.texture, piece.hidden, piece.relative_pos,
                       (tile_data.pos_mods[0], tile_data.pos_mods[1], tile_data.pos_mods[2] + piece.mod_w),
                       tile_data.directions, tile_data.vision, tile_data.actions)
        pieces.append(IsoSprite(*pos_data, data))

    return pieces


def generate_iso_data_other(key):
    """
    Finds the iso data but for special tiles not found in the normal data.
    :param key: the key for this data
    :return: the iso data.
    """
    tile_data = tiles.OTHER_TEXTURES[key]
    pieces = []
    for piece in tile_data.pieces:
        data = IsoData(piece.texture, piece.hidden, piece.relative_pos,
                       (tile_data.pos_mods[0], tile_data.pos_mods[1], tile_data.pos_mods[2] + piece.mod_w),
                       tile_data.directions, tile_data.vision, tile_data.actions)
        pieces.append(data)

    return pieces
