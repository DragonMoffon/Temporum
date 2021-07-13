import math

import numpy as np
import json
import time

import arcade

import isometric
import constants as c
import interaction
import tiles

CHECK_DIR = (1, 0), (0, 1), (1, 1)
INV = {'mouse': 'player', 'player': 'mouse'}


class Tile:

    def __init__(self):
        self.pieces: list[isometric.IsoSprite] = []
        self.directions = [1, 1, 1, 1]
        self.available_actions: dict[str, list] = {}

    def update(self, other):
        """
        this updates the directions, and the availble actions of the tile.
        :param other: A IsoSprite that should be in the tile.
        """
        if other not in self.pieces:
            self.pieces.append(other)

        self.mix_directions(other.direction)
        actions = list(set(self.available_actions.keys()) | set(other.actions))
        for action in actions:
            if action not in self.available_actions:
                self.available_actions[action] = [other]
            elif other not in self.available_actions[action]:
                self.available_actions[action].append(other)
            elif other in self.available_actions[action] and action not in other.actions:
                self.available_actions[action].remove(other)

    def mix_directions(self, other):
        self.directions = [dirs*other[index] for index, dirs in enumerate(self.directions)]

    def solve_direction(self, index):
        for piece in self.pieces:
            if not piece.directions[index]:
                return False
        return True

    def add(self, other):
        if other not in self.pieces:
            other.tile = self
            self.pieces.append(other)
            self.mix_directions(other.direction)
            for action in other.actions:
                if action not in self.available_actions:
                    self.available_actions[action] = [other]
                else:
                    self.available_actions[action].append(other)

    def remove(self, other):
        if other in self.pieces:
            other.tile = None
            self.pieces.remove(other)
            for index, direction in enumerate(other.direction):
                if not direction:
                    self.directions[index] = self.solve_direction(index)

            for action in other.actions:
                self.available_actions[action].remove(other)
                if not len(self.available_actions[action]):
                    self.available_actions.pop(action)


class DisplayHandler:

    def __init__(self, map_handler):
        self.states = {'wall': 0, 'cover': 0, 'poi': 0}
        self.state_methods = {'wall': self.wall_switch, 'cover': self.cover_switch, 'poi': self.poi_switch}
        self.reapply_methods = {'wall': self.wall_reapply, 'cover': self.cover_reapply, 'poi': self.poi_reapply}
        self.map_handler = map_handler
        self.all_walls = 1

    def mod_state(self, direction, identifier):
        self.states[identifier] = (self.states[identifier] + direction) % 3
        self.state_methods[identifier]()

    def update_states(self):
        for method in self.state_methods.values():
            method()

    def reapply(self, room):
        for method in self.reapply_methods.values():
            method(room)

    def wall_reapply(self, room):
        added_tiles = []
        if self.states['wall'] != 2:
            if not room.shown:
                added_tiles.extend(room.room_walls)
                room.shown = True
        c.iso_show(added_tiles)

    def cover_reapply(self, room):
        pass

    def poi_reapply(self, room):
        pass

    def wall_switch(self):
        removed_tiles = []
        if self.states['wall'] == 2:
            if self.all_walls != -1:
                self.map_handler.input_hide(second_args=['wall'])
                self.all_walls = -1
        elif self.states['wall']:
            for room in self.map_handler.current_rooms.values():
                if room is not None and room.shown:
                    removed_tiles.extend(room.room_walls)
                    room.shown = False
            self.all_walls = 0
        else:
            if self.all_walls != 1:
                self.map_handler.input_show(second_args=['wall'])
                self.all_walls = True

        c.iso_hide(removed_tiles)

    def cover_switch(self):
        pass

    def poi_switch(self):
        pass


class MapHandler:

    def __init__(self, game_view):
        # Read the map. This will later be a list of maps depending on the area.
        self.game_view = game_view
        self.current_location = "WorkroomEntrance"
        self.map = arcade.read_tmx(f"tiled/tilemaps/{self.current_location}.tmx")
        self.poi_data = json.load(open(f"data/{self.current_location}.json"))
        self.display_handler = DisplayHandler(self)

        # Save the layers for the map in a dictionary
        self.layers: dict[str, (dict, isometric.IsoLayer)] = {'1': {'floor': None, 'wall': None,
                                                                    'poi': None, 'room': None},
                                                              '2': {'floor': None, 'wall': None,
                                                                    'poi': None, 'room': None}}
        self.ground_layer: isometric.IsoLayer = None
        self.map_width, self.map_height = self.map.map_size
        self.map_size = [self.map_width, self.map_height]
        self.full_map = np.empty(self.map_size, Tile)
        c.set_map_size(self.map_size)
        self.rooms = {'1': {}}
        self.current_rooms: dict[str, isometric.IsoRoom] = {'player': None, 'mouse': None}
        self.load_map(self.map)

    def load_map(self, map_data):
        """
        The load map scrip runs through the provided map and creates an IsoLayer object for each layer which stores many
        different values, these include the raw tile values as a 2D array and the tile sprites in a 2D numpy array.

        These IsoLayers are then stored by their name in a dictionary.
        :param map_data: The tmx map the layers are loaded from
        """

        with open(f"data/{self.current_location}.json") as json_file:
            json_data = json.load(json_file)
        for layer_num, layer_data in enumerate(map_data.layers):
            location = layer_data.name.split(" ")

            if layer_data.properties is not None:
                shown = layer_data.properties.get('shown', True)
            else:
                print(f"Layer: {layer_data.name} does not have required properties."
                      f" It will not be loaded, please check through your Tiled Map for errors")
                continue

            # Create the IsoList for the tiles, renames the layers raw tile 2D array for better readability,
            # and create the 2D numpy array
            tile_list = []
            map_data = layer_data.layer_data
            tile_map = np.empty(self.map_size, list)

            def find_tile_walls(current_room, data_layer):
                walls = []
                check_self = False
                for direction in CHECK_DIR:
                    d_x = e_x + direction[0]
                    d_y = e_y + direction[1]
                    if 0 <= d_x < self.map_width and 0 <= d_y < self.map_height:
                        if data_layer[d_y][d_x] != current_room:
                            wall_tile = self.layers['1']['wall'].tile_map[d_x][d_y]
                            if wall_tile is not None:
                                walls.extend(wall_tile)
                            else:
                                check_self = True
                    else:
                        check_self = True

                if check_self:
                    wall_tile = self.layers['1']['wall'].tile_map[e_x][e_y]
                    if wall_tile is not None:
                        walls.extend(wall_tile)

                return walls

            def generate_room(data):
                if data not in self.rooms[location[0]]:
                    room = isometric.IsoRoom(arcade.SpriteList())

                    room.room_walls.extend(find_tile_walls(data, map_data))

                    self.rooms[location[0]][data] = room

                else:
                    wall_tiles = find_tile_walls(data, map_data)
                    for tile in wall_tiles:
                        if tile not in self.rooms[location[0]][data].room_walls:
                            self.rooms[location[0]][data].room_walls.append(tile)

            def generate_poi(data):
                poi_data = json_data['interact'][str(data)]
                data = poi_data['tile']

                current_tiles = isometric.find_poi_sprites(data, interaction.load_conversation(poi_data['interaction']),
                                                           (e_x, e_y))
                tile_list.extend(current_tiles)
                tile_map[e_x, e_y] = current_tiles
                for tile in current_tiles:
                    if self.full_map[tile.e_x, tile.e_y] is None:
                        self.full_map[tile.e_x, tile.e_y] = Tile()
                    self.full_map[tile.e_x, tile.e_y].add(tile)

            def generate_door(data):
                door_data = json_data['door'].get(str(data))
                tile_data = door_data['tiles']
                target_id = data - 16

                current_tile = isometric.find_toggle_sprites(tile_data, target_id, (e_x, e_y))
                tile_list.append(current_tile)
                tile_map[e_x, e_y] = current_tile
                if self.full_map[e_x, e_y] is None:
                    self.full_map[e_x, e_y] = Tile()
                self.full_map[e_x, e_y].add(current_tile)

            def generate_layer(data):
                # take the x and y coord of the tile in the map data to create the isometric position
                current_tiles = isometric.find_iso_sprites(data, (e_x, e_y))
                tile_list.extend(current_tiles)
                tile_map[e_x, e_y] = current_tiles
                for tile in current_tiles:
                    if self.full_map[tile.e_x, tile.e_y] is None:
                        self.full_map[tile.e_x, tile.e_y] = Tile()
                    self.full_map[tile.e_x, tile.e_y].add(tile)

            generation_functions = {'floor': generate_layer, 'wall': generate_layer,
                                    'poi': generate_poi, 'room': generate_room,
                                    'door': generate_door}

            # Loop through the tile data.
            for e_y, row in enumerate(map_data):
                for e_x, tile_value in enumerate(row):
                    # If there is a tile in found in the data create the appropriate tile.
                    if tile_value:
                        generation_functions.get(location[-1], generate_layer)(tile_value)

            self.layers[location[0]][location[1]] = isometric.IsoLayer(layer_data, map_data, tile_list, tile_map, shown)
        self.ground_layer = self.layers['1']['floor'].map_data
        self.initial_show()

    def input_show(self, first_args='1', second_args=('wall', 'poi', 'door')):
        shown_tiles = []
        for args in first_args:
            for locator_args in second_args:
                layer = self.layers[args][locator_args]
                shown_tiles.extend(layer.tiles)
        c.iso_show(shown_tiles)

    def input_hide(self, first_args='1', second_args=()):
        hidden_tiles = []
        for args in first_args:
            for locator_args in second_args:
                layer = self.layers[args][locator_args]
                hidden_tiles.extend(layer.tiles)

        c.iso_hide(hidden_tiles)

    def initial_show(self):
        shown_layers = []
        for key, layer in self.layers['1'].items():
            if layer.shown and key != 'floor':
                shown_layers.append(key)
        self.input_show(second_args=shown_layers)
        c.set_floor(self.layers['1']['floor'].tiles)

    def run_display(self, setter, e_x, e_y):
        room = self.layers['1']['room'].map_data[e_y][e_x]
        if room:
            room = self.rooms['1'][room]
            if self.current_rooms[setter] != room:
                if self.current_rooms[setter] is not None and not self.current_rooms[setter].shown:
                    if self.current_rooms[INV[setter]] != room:
                        self.display_handler.reapply(self.current_rooms[setter])
                self.current_rooms[setter] = room
                self.display_handler.update_states()

    def debug_draw(self, a_star=False, display_draw=False):
        if a_star:
            pass

        if display_draw:
            arcade.draw_text(str(self.display_handler.states), 0, 0, arcade.color.WHITE)
