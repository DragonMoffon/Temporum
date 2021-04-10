import numpy as np

import arcade

import tiles
import isometric
import algorithms


class MapHandler:

    def __init__(self):
        # Read the map. This will later be a list of maps depending on the area.
        self.map = arcade.read_tmx("tiled/tilemaps/mvp.tmx")

        # Save the layers for the map in a dictionary
        self.layers = None
        self.ground_layer = None
        self.map_width, self.map_height = 0, 0
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
        self.layers = {}
        for layer_num, layer_data in enumerate(map_data.layers):
            # Create the IsoList for the tiles, renames the layers raw tile 2D array for better readability,
            # and create the 2D numpy array
            tile_list = isometric.IsoList()
            map_data = layer_data.layer_data
            tile_map = np.empty((len(map_data[0]), len(map_data)), isometric.IsoSprite)

            # Find the center Z modifier of the layer any tile ordering can be done properly.
            if layer_data.properties is not None and "z_mod" in layer_data.properties:
                z_mod = layer_data.properties["z_mod"]
            else:
                z_mod = 0

            # Loop through the tile data.
            for e_y, y in enumerate(map_data):
                for e_x, x in enumerate(y):
                    # If there is a tile in found in the data create the appropriate tile.
                    if x:
                        # take the x and y coord of the tile in the map data to create he isometric position
                        iso_x, iso_y, iso_z = isometric.cast_to_iso(e_x, e_y, map_data, tile_list, z_mod)
                        tile = isometric.IsoSprite(e_x, e_y, iso_x, iso_y, iso_z, tiles.find_iso_data(x))
                        tile_list.append(tile)
                        tile_map[e_x, e_y] = tile
            tile_list.reorder_isometric()
            self.layers[layer_data.name] = isometric.IsoLayer(layer_data, map_data, tile_list, tile_map)
        self.ground_layer = self.layers['ground_layer'].map_data
        self.map_width, self.map_height = len(self.ground_layer), len(self.ground_layer[0])

    def apply_shown(self):
        all_tiles = isometric.IsoList()
        for layer in self.layers.values():
            if layer.shown:
                all_tiles.extend(layer.tiles)
        all_tiles.reorder_isometric()
        return all_tiles

    def debug_draw(self, a_star=False):
        if a_star:
            self.path_finding_map.draw()
