import numpy as np
import json
from dataclasses import dataclass

import arcade

import algorithms
import isometric
import constants as c
import interaction

CHECK_DIR = (1, 0), (0, 1), (1, 1)
INV = {'mouse': 'player', 'player': 'mouse'}


class Tile:

    def __init__(self):
        self.pieces: list[isometric.IsoSprite] = []
        self.directions = [1, 1, 1, 1]
        self.vision = [1, 1, 1, 1]
        self.neighbours: list[Tile, Tile, Tile, Tile] = [None, None, None, None]
        self.location: tuple[int, int] = (0, 0)
        self.available_actions: dict[str, list] = {}

    def update(self, other):
        """
        this updates the directions, and the available actions of the tile.
        :param other: A IsoSprite that should be in the tile.
        """

        if other not in self.pieces:
            self.pieces.append(other)

        self.find_direction_vision()

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

    def mix_vision(self, other):
        self.vision = [vision*other[index] for index, vision in enumerate(self.vision)]
        if 0 in self.vision:
            c.add_wall(self)
        else:
            c.remove_wall(self)

    def solve_direction(self, index):
        for piece in self.pieces:
            if not piece.direction[index]:
                return False
        return True

    def solve_vission(self, index):
        for piece in self.pieces:
            if not piece.vision_direction[index]:
                return False
        return True

    def find_direction_vision(self):
        for index, dirs in enumerate(self.directions):
            self.directions[index] = self.solve_direction(index)
            self.vision[index] = self.solve_vission(index)
        if 0 in self.vision:
            c.add_wall(self)
        else:
            c.remove_wall(self)

    def add(self, other):
        if other not in self.pieces:
            other.tile = self
            self.pieces.append(other)
            self.mix_directions(other.direction)
            self.mix_vision(other.vision_direction)
            for action in other.actions:
                if action not in self.available_actions:
                    self.available_actions[action] = [other]
                else:
                    self.available_actions[action].append(other)

    def remove(self, other):
        if other in self.pieces:
            other.tile = None
            self.pieces.remove(other)
            self.find_direction_vision()

            for action in other.actions:
                self.available_actions[action].remove(other)
                if not len(self.available_actions[action]):
                    self.available_actions.pop(action)

    def __le__(self, other):
        return id(self) <= id(other)

    def __lt__(self, other):
        return id(self) < id(other)


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
        self.current_location = "demo_1"
        self.map = arcade.read_tmx(f"tiled/tilemaps/{self.current_location}.tmx")
        self.poi_data = json.load(open(f"data/{self.current_location}.json"))
        self.display_handler = DisplayHandler(self)

        # Save the layers for the map in a dictionary
        self.layers: dict[str, (dict, isometric.IsoLayer)] = {'1': {'floor': None, 'wall': None,
                                                                    'poi': None, 'room': None},
                                                              '2': {'floor': None, 'wall': None,
                                                                    'poi': None, 'room': None}}

        self.toggle_sprites = {}
        self.map_width, self.map_height = self.map.map_size
        self.map_size = [self.map_width, self.map_height]
        self.full_map = np.empty(self.map_size, Tile)
        self.map_bots = []
        c.set_map_size(self.map_size)
        self.rooms = {'1': {}}
        self.current_rooms: dict[str, isometric.IsoRoom] = {'player': None, 'mouse': None}

    def load_map(self, map_data):
        """
        The load map scrip runs through the provided map and creates an IsoLayer object for each layer which stores many
        different values, these include the raw tile values as a 2D array and the tile sprites in a 2D numpy array.

        These IsoLayers are then stored by their name in a dictionary.
        :param map_data: The tmx map the layers are loaded from
        """
        self.game_view.reset_bots()
        self.map_bots = []

        @dataclass()
        class BotData:
            x: int = 0
            y: int = 0
            bot_type: str = "basic"
            shown: bool = False

        self.toggle_sprites = {}

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
                poi_data = json_data['interact'].get(str(data), None)
                if poi_data is not None:
                    data = poi_data['tile']

                    current_tiles = isometric.find_poi_sprites(data,
                                                               interaction.load_conversation(poi_data['interaction']),
                                                               (e_x, e_y))
                    tile_list.extend(current_tiles)
                    tile_map[e_x, e_y] = current_tiles
                    for tile in current_tiles:
                        if self.full_map[tile.e_x, tile.e_y] is None:
                            self.full_map[tile.e_x, tile.e_y] = Tile()
                        self.full_map[tile.e_x, tile.e_y].add(tile)

            def generate_door(data):
                door_data = json_data['door'].get(str(data))
                if door_data is not None:
                    tile_data = door_data['tiles']
                    target_id = data - 16

                    current_tile = isometric.find_toggle_sprites(tile_data, target_id, (e_x, e_y))
                    tile_list.append(current_tile)
                    tile_map[e_x, e_y] = current_tile
                    if self.full_map[e_x, e_y] is None:
                        self.full_map[e_x, e_y] = Tile()
                    self.full_map[e_x, e_y].add(current_tile)

                    if target_id not in self.toggle_sprites:
                        self.toggle_sprites[target_id] = []
                    self.toggle_sprites[target_id].append(current_tile)

            def generate_layer(data):
                # take the x and y coord of the tile in the map data to create the isometric position
                current_tiles = isometric.find_iso_sprites(data, (e_x, e_y))
                tile_list.extend(current_tiles)
                tile_map[e_x, e_y] = current_tiles
                for tile in current_tiles:
                    if self.full_map[tile.e_x, tile.e_y] is None:
                        self.full_map[tile.e_x, tile.e_y] = Tile()
                    self.full_map[tile.e_x, tile.e_y].add(tile)

            def generate_isoactor(data):
                isoactor_data = json_data['character'].get(str(data))
                if isoactor_data is not None:
                    if isoactor_data['type'] == "player":
                        self.game_view.player.new_pos(e_x, e_y)
                    else:
                        new_bot = BotData(e_x, e_y, isoactor_data['type'], isoactor_data['start_active'])
                        self.map_bots.append(new_bot)

            generation_functions = {'floor': generate_layer, 'wall': generate_layer,
                                    'poi': generate_poi, 'room': generate_room,
                                    'door': generate_door, 'char': generate_isoactor}

            # Loop through the tile data.
            for e_y, row in enumerate(map_data):
                for e_x, tile_value in enumerate(row):
                    # If there is a tile in found in the data create the appropriate tile.
                    if tile_value:
                        generation_functions.get(location[-1], generate_layer)(tile_value)

            self.layers[location[0]][location[1]] = isometric.IsoLayer(layer_data, map_data, tile_list, tile_map, shown)
        algorithms.find_neighbours(self.full_map)
        for bot in self.map_bots:
            if bot.shown:
                self.game_view.new_bot(bot)
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

    def toggle_target_sprites(self, target_id):
        if target_id in self.toggle_sprites:
            for door in self.toggle_sprites[target_id]:
                door.toggle_states()

    def debug_draw(self, a_star=False, display_draw=False):
        if a_star:
            # A debugging draw that creates 4 points for each tile. one for each direction N, E, S, W.
            # The point is red if it is not a connection, white if it is.
            if self.full_map is not None:
                dirs = ((0, 0.25), (0.25, 0), (0, -0.25), (-0.25, 0))
                for x_dex, point_row in enumerate(self.full_map):
                    for y_dex, value in enumerate(point_row):
                        if value is not None:
                            for dir_dex, direction in enumerate(dirs):
                                t_x = x_dex + direction[0]
                                t_y = y_dex + direction[1]
                                iso_x, iso_y, iso_z = isometric.cast_to_iso(t_x, t_y)
                                if value.neighbours[dir_dex] is None:
                                    arcade.draw_point(iso_x, iso_y - 60, arcade.color.RADICAL_RED, 5)
                                elif not value.directions[dir_dex]:
                                    arcade.draw_point(iso_x, iso_y - 60, arcade.color.GREEN, 5)
                                else:
                                    arcade.draw_point(iso_x, iso_y - 60, arcade.color.WHITE, 5)

            # draws a line from a tile to the tile it came from. they all lead back to the player.
            if self.game_view.player.path_finding_data is not None:
                for tile_node in self.game_view.player.path_finding_data[0]:
                    came_from = self.game_view.player.path_finding_data[0][tile_node]
                    if came_from is not None:
                        start_x, start_y, z = isometric.cast_to_iso(*tile_node.location)
                        end_x, end_y, z = isometric.cast_to_iso(*came_from.location)
                        arcade.draw_line(start_x, start_y-60, end_x, end_y-60, arcade.color.RADICAL_RED)

        if display_draw:
            arcade.draw_text(str(self.display_handler.states), 0, 0, arcade.color.WHITE)
