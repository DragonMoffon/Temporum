import numpy as np
import json
from dataclasses import dataclass
import math
import time

import arcade

import algorithms
import isometric
import constants as c
import interaction
from vision import VisionCalculator
from map_tile import Tile

# GATES and POI_LIGHTS are the highlights used to show the player points of interest and gates. each index represents a
# direction in order: south, east, north, west
GATES = {index: data for index, data in enumerate(isometric.generate_iso_data_other("gate_highlight"))}
POI_LIGHTS = {index: data for index, data in enumerate(isometric.generate_iso_data_other("poi_highlight"))}


class Map:
    """
    Map holds the tiles and other data for a single tmx map.
    """
    def __init__(self, game_view, data, location="tutorial"):
        self.game_view = game_view

        # The str location of the tmx data and the json data.
        self.location = location
        self.tmx_map = arcade.read_tmx(f"tiled/tilemaps/{self.location}.tmx")
        self.item_data = data[location]

        # the maps unique vision handler.
        self.lit = location == "tutorial"
        self.vision_handler = VisionCalculator(game_view.window, game_view.player, self.lit)

        # The size of the map.
        self.map_size = self.tmx_map.map_size
        self.map_width, self.map_height = self.map_size

        # The bots
        self.bots = []

        # If anything on the map has changed
        self.changed = True

        # The data of each layer, rooms, and tiles.
        self.toggle_sprites = {}
        self.layers = {}
        self.rooms = {}
        self.tile_map = np.empty(self.map_size, Tile)

        # sprites with animations.
        self.animated_sprites = []

    def load_map(self):
        """
        The load map scrip runs through the provided map and creates an
        IsoLayer object for each layer which stores many
        different values, these include the raw tile values as a 2D array
         and the tile sprites in a 2D numpy array.

        These IsoLayers are then stored by their name in a dictionary.
        """

        self.game_view.reset_bots()
        self.bots = []
        self.vision_handler.setup(tuple(self.map_size))
        self.animated_sprites = []

        c.set_map_size(self.map_size)

        @dataclass()
        class BotData:
            x: int = 0
            y: int = 0
            bot_type: str = "basic"
            shown: bool = False
            ai_type: str = "avoid"

        self.toggle_sprites = {}

        for layer_num, layer_data in enumerate(self.tmx_map.layers):
            location = layer_data.name

            if layer_data.properties is not None:
                shown = layer_data.properties.get('shown', True)
            else:
                shown = True

            # Create the IsoList for the tiles, renames the layer's raw tile 2D array for better readability,
            # and create the 2D numpy array
            tile_list = []
            map_data = layer_data.layer_data
            tile_map = np.empty(self.map_size, list)

            def generate_poi(data):
                poi_data = self.item_data['interact'].get(str(data), None)
                if poi_data is not None:
                    data = poi_data['tile']

                    current_tiles = isometric.find_poi_sprites(data,
                                                               interaction.load_conversation(poi_data['interaction']),
                                                               (e_x, e_y))

                    tile_directions = set()
                    tile_list.extend(current_tiles)
                    tile_map[e_x, e_y] = list(current_tiles)
                    for tile in current_tiles:
                        if len(tile.animations):
                            self.animated_sprites.append(tile)

                        pos = (tile.e_x, tile.e_y)
                        if pos not in tile_directions:
                            tile_directions.add(pos)
                        if self.tile_map[pos] is None:
                            self.tile_map[pos] = Tile(pos, self)
                        self.tile_map[pos].add(tile)

                    if len(current_tiles):
                        for tile in current_tiles:
                            for i in range(4):
                                direction = (i % 2 * ((math.floor(i / 2) * -2) + 1),
                                             (1 - i % 2) * ((math.floor(i / 2) * -2) + 1))
                                if (tile.e_x + direction[0], tile.e_y + direction[1]) not in tile_directions:
                                    highlight = isometric.IsoSprite(tile.e_x, tile.e_y, POI_LIGHTS[i])
                                    tile_list.append(highlight)
                                    tile_map[e_x, e_y].append(highlight)
                                    self.tile_map[tile.e_x, tile.e_y].add(highlight)

            def generate_door(data):
                door_data = self.item_data['door'].get(str(data))
                if door_data is not None:
                    tile_data = door_data['tiles']
                    target_id = data - 16

                    current_tile = isometric.find_toggle_sprites(tile_data, target_id, (e_x, e_y))
                    tile_list.append(current_tile)
                    tile_map[e_x, e_y] = current_tile
                    if self.tile_map[e_x, e_y] is None:
                        self.tile_map[e_x, e_y] = Tile((e_x, e_y), self)
                    self.tile_map[e_x, e_y].add(current_tile)

                    if target_id not in self.toggle_sprites:
                        self.toggle_sprites[target_id] = []
                    self.toggle_sprites[target_id].append(current_tile)

            def generate_gate(data):
                gate_data = self.item_data['gates'][str(data)]
                if self.tile_map[e_x, e_y] is None:
                    current_tile = Tile((e_x, e_y), self)
                    self.tile_map[e_x, e_y] = current_tile
                else:
                    current_tile = self.tile_map[e_x, e_y]

                rel_pos = e_x - gate_data['start'][0], e_y - gate_data['start'][1]
                next_pos = gate_data['position'][0] + rel_pos[0], gate_data['position'][1] + rel_pos[1]

                rel_gate_data = {"target": gate_data["target"], "land_pos": next_pos}

                current_tiles = []
                gate_tile = isometric.IsoGateSprite(e_x, e_y, GATES[4], rel_gate_data)
                tile_list.append(gate_tile)
                current_tiles.append(gate_tile)
                current_tile.light_add(gate_tile)

                for i in range(4):
                    direction = (i % 2 * ((math.floor(i/2)*-2) + 1), (1 - i % 2) * ((math.floor(i/2)*-2) + 1))
                    if (e_y+direction[1] > self.map_size[1] or e_x+direction[0] > self.map_size[0] or
                            (e_y+direction[1] < self.map_size[1] and e_x+direction[0] < self.map_size[0] and
                             map_data[e_y+direction[1]][e_x+direction[0]] != data)):
                        tile = isometric.IsoGateSprite(e_x, e_y, GATES[i], rel_gate_data)
                        current_tile.light_add(tile)
                        current_tiles.append(tile)
                        tile_list.append(tile)

                tile_map[e_x, e_y] = current_tiles

            def generate_decoration(data):
                # same as generate layer but takes a str not an int.
                generate_layer(str(data))

            def generate_layer(data):
                # find the pieces(individual sprites) that make up the IsoSprite.
                current_tiles = isometric.find_iso_sprites(data, (e_x, e_y))
                tile_list.extend(current_tiles)
                tile_map[e_x, e_y] = current_tiles
                for tile in current_tiles:
                    if len(tile.animations):
                        self.animated_sprites.append(tile)
                    if self.tile_map[tile.e_x, tile.e_y] is None:
                        self.tile_map[tile.e_x, tile.e_y] = Tile((e_x, e_y), self)
                    self.tile_map[tile.e_x, tile.e_y].add(tile)

            def generate_isoactor(data):
                isoactor_data = self.item_data['character'].get(str(data))
                if isoactor_data is not None:
                    if isoactor_data['type'] == "player":
                        self.game_view.player.new_pos(e_x, e_y)
                    elif isoactor_data['type'] == "dummy":
                        iso_data = isometric.generate_iso_data_other(isoactor_data['type'])
                        dummy = isometric.IsoSprite(e_x, e_y, *iso_data,
                                                    {'hit': isometric.IsoAnimation(
                                                        "assets/characters/iso_dummy.png",
                                                        (160, 320), (160, 0), 4, 1/12)})
                        tile_list.append(dummy)
                        tile_map[e_x, e_y] = dummy
                        self.animated_sprites.append(dummy)
                        if self.tile_map[e_x, e_y] is None:
                            self.tile_map[e_x, e_y] = Tile((e_x, e_y), self)
                        self.tile_map[e_x, e_y].add(dummy)
                    else:
                        new_bot = BotData(e_x, e_y, isoactor_data['type'], isoactor_data['start_active'])
                        self.bots.append(new_bot)

            generation_functions = {'floor': generate_layer, 'wall': generate_layer, 'gate': generate_gate,
                                    'poi': generate_poi, 'door': generate_door, 'char': generate_isoactor,
                                    'decoration': generate_decoration}

            # Loop through the tile data.
            for e_y, row in enumerate(map_data):
                for e_x, tile_value in enumerate(row):
                    # If there is a tile in found in the data create the appropriate tile.
                    if tile_value:
                        generation_functions.get(location, generate_layer)(tile_value)

            self.layers[location] = isometric.IsoLayer(layer_data, map_data, tile_list, tile_map, shown)

        c.set_floor(self.layers['floor'].tiles)
        algorithms.find_neighbours(self.tile_map)
        for bot in self.bots:
            if bot.shown:
                self.game_view.new_bot(bot)

    def strip_map(self):
        """
        complety remove all the sprites on this map from the iso list and the game view. So a new map can be loaded.
        """
        self.game_view.reset_bots()
        for row in self.tile_map:
            for tile in row:
                if tile is not None:
                    if self.game_view.player in tile.actors:
                        tile.light_remove(self.game_view.player)

                    c.iso_strip(tile.pieces)
                    c.iso_strip(tile.actors)

    def set_map(self):
        """
        show all the items from this map.
        """
        c.set_map_size(self.map_size)
        c.set_floor(self.layers['floor'].tiles)
        for row in self.tile_map:
            for tile in row:
                if tile is not None:
                    c.iso_extend(tile.pieces)
                    c.iso_extend(tile.actors)
        self.vision_handler.regenerate = 2

    def draw(self):
        self.vision_handler.draw()
        if self.vision_handler.recalculate == 1:
            self.hide_walls()
            self.vision_handler.recalculate = 0

    def hide_walls(self):
        """
        Based on the data generated by the vision handler. Find what tiles to show and what to hide.
        """
        s = time.time()
        checked = set()

        remove = []
        show = []
        for bot in self.game_view.current_ai:
            if self.vision_handler.vision_image.getpixel((bot.e_x, bot.e_y))[0]:
                c.iso_append(bot)
            else:
                c.iso_remove(bot)

        for x in self.tile_map:
            for y in x:
                if y is not None:
                    if not self.vision_handler.vision_image.getpixel(y.location)[0]:
                        if y not in checked:
                            if y.seen:
                                for piece in y.pieces:
                                    piece.alpha = 150
                                    piece.color = (95, 205, 228)
                            else:
                                for piece in y.pieces:
                                    piece.alpha = 0
                    else:
                        y.seen = True
                        for piece in y.pieces:
                            piece.alpha = 255

                            if self.lit:
                                color = 255
                            else:
                                # the distance is the value normalised and the map size relative to 15.
                                # so dist/255 * map/15 or (map*dist)/(255*15) or (map*dist)/3825
                                distance = (self.vision_handler.vision_image.getpixel(y.location)[1] *
                                            self.map_size[0]/3825)

                                color = max(int(255 - 255*distance), 0)
                            piece.color = (color, color, color)

                        for index, tile in enumerate(y.neighbours):
                            if (tile is not None and tile not in checked and
                                    not self.vision_handler.vision_image.getpixel(tile.location)[0] and
                                    y.vision[index] and not tile.vision[(index+2) % 4]):
                                checked.add(tile)
                                tile.seen = True
                                for piece in tile.pieces:
                                    piece.alpha = 255

                                    if self.lit:
                                        color = 255
                                    else:
                                        # the distance is the value normalised and the map size relative to 15.
                                        # so dist/255 * map/15 or (map*dist)/(255*15) or (map*dist)/3825
                                        distance = self.vision_handler.vision_image.getpixel(y.location)[1] * \
                                                   self.map_size[0] / 3825

                                        color = max(int(255 - 255 * distance), 0)
                                    piece.color = (color, color, color)

    def check_seen(self, location):
        return bool(self.vision_handler.vision_image.getpixel(location)[0])


class MapHandler:

    def __init__(self, game_view):
        # Read the map. This will later be a list of maps depending on the area.
        self.game_view = game_view

        with open("data/map_data.json") as map_data:
            self.map_data = json.load(map_data)

        self.maps = {}

        self.map = Map(game_view, self.map_data, 'tutorial')
        self.maps['tutorial'] = self.map

    def use_gate(self, gate_data):
        if gate_data['target'] == "GameFinish":
            self.game_view.window.show_end()
        else:
            self.map.strip_map()
            next_map = self.maps.get(gate_data['target'])
            if next_map is None:
                next_map = Map(self.game_view, self.map_data, gate_data['target'])
                self.maps[gate_data['target']] = next_map
                self.map = next_map
                self.load_map()
            else:
                self.map = next_map
                self.map.set_map()

            self.game_view.player.set_grid(self.map.tile_map)
            self.game_view.player.new_map_pos(*gate_data['land_pos'])
            self.game_view.selected_tile.new_pos(self.game_view.player.e_x, self.game_view.player.e_y)
            self.game_view.set_view(self.game_view.player.center_x-c.SCREEN_WIDTH//2,
                                    self.game_view.player.center_y-c.SCREEN_HEIGHT//2)
            self.game_view.pending_motion = []
            self.game_view.current_motion = None
            self.game_view.motion = False
            c.iso_append(self.game_view.player)

    def load_map(self):
        """
        The load map scrip runs through the provided map and creates an IsoLayer object for each layer which stores many
        different values, these include the raw tile values as a 2D array and the tile sprites in a 2D numpy array.

        These IsoLayers are then stored by their name in a dictionary.
        """
        self.map.load_map()
        self.initial_show()

    def input_show(self, second_args=('wall', 'poi', 'door')):
        shown_tiles = []
        for locator_args in second_args:
            layer = self.layers[locator_args]
            shown_tiles.extend(layer.tiles)
        c.iso_extend(shown_tiles)

    def initial_show(self):
        shown_layers = []
        for key, layer in self.layers.items():
            if layer.shown and key != 'floor':
                shown_layers.append(key)
        self.input_show(second_args=shown_layers)
        c.set_floor(self.layers['floor'].tiles)

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

    @property
    def layers(self):
        return self.map.layers

    @property
    def map_size(self):
        return self.map.map_size

    @property
    def map_width(self):
        return self.map.map_width

    @property
    def map_height(self):
        return self.map.map_height

    @property
    def full_map(self):
        return self.map.tile_map

    @property
    def rooms(self):
        return self.map.rooms

    @property
    def toggle_sprites(self):
        return self.map.toggle_sprites

    @property
    def map_bots(self):
        return self.map.bots

    def draw(self):
        self.map.draw()
