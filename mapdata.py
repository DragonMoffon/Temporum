import numpy as np

import arcade

import tiles
import isometric
import algorithms
import constants as c

CHECK_DIR = (1, 0), (0, 1), (1, 1)
INV = {'mouse': 'player', 'player': 'mouse'}


class DisplayHandler:

    def __init__(self, map_handler):
        self.states = {'wall': 0, 'cover': 0, 'poi': 0}
        self.state_methods = {'wall': self.wall_switch, 'cover': self.cover_switch, 'poi': self.poi_switch}
        self.map_handler = map_handler

    def mod_state(self, direction, identifier):
        self.states[identifier] = (self.states[identifier] + direction) % 3
        self.state_methods[identifier]()

    def update_states(self):
        for method in self.state_methods.values():
            method()

    def wall_switch(self):
        removed_tiles = []
        if self.states['wall'] == 2:
            self.map_handler.input_hide(second_args=['wall'])
        elif self.states['wall']:
            for room in self.map_handler.current_rooms.values():
                if room is not None and room.shown:
                    removed_tiles.extend(room.room_walls)
                    room.shown = False
        else:
            self.map_handler.input_show(second_args=['wall'])

        c.iso_hide(removed_tiles)

    def cover_switch(self):
        pass

    def poi_switch(self):
        pass


class MapHandler:

    def __init__(self):
        # Read the map. This will later be a list of maps depending on the area.
        self.map = arcade.read_tmx("tiled/tilemaps/mvp.tmx")
        self.display_handler = DisplayHandler(self)

        # Save the layers for the map in a dictionary
        self.layers: dict[str, (dict, isometric.IsoLayer)] = {"map": {'1': {'floor': None, 'wall': None, 'poi': None},
                                                                      '2': {}},
                                                              "data": {'1': {'room': None}, '2': {}}}
        self.ground_layer = None
        self.map_width, self.map_height = self.map.map_size
        self.map_size = [self.map_width, self.map_height]
        self.rooms = {'1': {}}
        self.current_rooms: dict[str, isometric.IsoRoom] = {'player': None, 'mouse': None}
        self.load_map(self.map)

        # The path finding data
        self.path_finding_map = algorithms.PathFindingGrid(self)

    def load_map(self, map_data):
        """
        The load map scrip runs through the provided map and creates an IsoLayer object for each layer which stores many
        different values, these include the raw tile values as a 2D array and the tile sprites in a 2D numpy array.

        These IsoLayers are then stored by their name in a dictionary.
        :param map_data: The tmx map the layers are loaded from
        """

        for layer_num, layer_data in enumerate(map_data.layers):
            # Find the center Z modifier of the layer any tile ordering can be done properly.
            z_mod = 0
            shown = True
            location = layer_data.name.split(" ")

            if layer_data.properties is not None:
                if "z_mod" in layer_data.properties:
                    z_mod = layer_data.properties["z_mod"]
                if "shown" in layer_data.properties:
                    shown = layer_data.properties['shown']
            else:
                print(f"Layer: {layer_data.name} does not have required properties."
                      f" It will not be loaded, please check through your Tiled Map for errors")
                continue

            # Create the IsoList for the tiles, renames the layers raw tile 2D array for better readability,
            # and create the 2D numpy array
            tile_list = []
            map_data = layer_data.layer_data
            if location[0] == 'map':
                tile_map = np.empty(self.map_size, list)
            else:
                tile_map = None

            def find_tile_walls(current_room, data_layer):
                walls = []
                check_self = False
                for direction in CHECK_DIR:
                    d_x = e_x + direction[0]
                    d_y = e_y + direction[1]
                    if 0 <= d_x < self.map_width and 0 <= d_y < self.map_height:
                        if data_layer[d_y][d_x] != current_room:
                            wall_tile = self.layers['map']['1']['wall'].tile_map[d_x][d_y]
                            if wall_tile is not None:
                                walls.extend(wall_tile)
                            else:
                                check_self = True
                    else:
                        check_self = True

                if check_self:
                    wall_tile = self.layers['map']['1']['wall'].tile_map[e_x][e_y]
                    if wall_tile is not None:
                        walls.extend(wall_tile)

                return walls

            # Loop through the tile data.
            for e_y, y in enumerate(map_data):
                for e_x, x in enumerate(y):
                    # If there is a tile in found in the data create the appropriate tile.
                    if x:
                        if location[0] == 'data':
                            if location[2] == 'room':
                                if x not in self.rooms[location[1]]:
                                    room = isometric.IsoRoom(arcade.SpriteList())

                                    room.room_walls.extend(find_tile_walls(x, map_data))

                                    self.rooms[location[1]][x] = room

                                else:
                                    wall_tiles = find_tile_walls(x, map_data)
                                    for tile in wall_tiles:
                                        if tile not in self.rooms[location[1]][x].room_walls:
                                            self.rooms[location[1]][x].room_walls.append(tile)

                        else:
                            # take the x and y coord of the tile in the map data to create the isometric position
                            current_tiles = tiles.find_iso_sprites(x, (e_x, e_y, self.map_size, z_mod))
                            tile_list.extend(current_tiles)
                            tile_map[e_x, e_y] = current_tiles

            self.layers[location[0]][location[1]][location[2]] = isometric.IsoLayer(layer_data, map_data,
                                                                                    tile_list, tile_map, shown)
        self.ground_layer = self.layers['map']['1']['floor'].map_data
        self.initial_show()

    def input_show(self, first_args='1', second_args=('floor', 'wall', 'poi')):
        shown_tiles = []
        for args in first_args:
            for locator_args in second_args:
                layer = self.layers['map'][args][locator_args]
                shown_tiles.extend(layer.tiles)
        c.iso_show(shown_tiles)

    def input_hide(self, first_args='1', second_args=()):
        hidden_tiles = []
        for args in first_args:
            for locator_args in second_args:
                layer = self.layers['map'][args][locator_args]
                hidden_tiles.extend(layer.tiles)

        c.iso_hide(hidden_tiles)

    def initial_show(self):
        shown_layers = []
        for key, layer in self.layers['map']['1'].items():
            if layer.shown:
                shown_layers.append(key)
        self.input_show(second_args=shown_layers)

    def run_display(self, setter, e_x, e_y):
        room = self.layers['data']['1']['room'].map_data[e_y][e_x]
        if room:
            room = self.rooms['1'][room]
            if self.current_rooms[setter] != room:
                if self.current_rooms[setter] is not None and not self.current_rooms[setter].shown:
                    if self.current_rooms[INV[setter]] != room:
                        c.iso_show(self.current_rooms[setter].room_walls)
                        self.current_rooms[setter].shown = True
                self.current_rooms[setter] = room
                self.display_handler.update_states()

    def debug_draw(self, a_star=False, display_draw=False):
        if a_star:
            self.path_finding_map.draw()

        if display_draw:
            arcade.draw_text(str(self.display_handler.states), 0, 0, arcade.color.WHITE)
