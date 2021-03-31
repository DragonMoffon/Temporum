import arcade
import tiles
import isometric


def xy_rotate_map(value_map):
    """
    :param value_map: The 2D array which holds the data to be rotated
    :return: It returns the rotated map. The X rows become the Y columns and vice-versa.

    The function rotates a 2D list array. so that the X rows become the Y columns.
    If looking at at array that has x = 0, y = 0 in the top left corner, like so:
    [0, 0, 1, 0],
    [1, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 1, 0, 0],
    [1, 0, 0, 1]

    It would be rotated and flipped to become:
    [1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1],
    [0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0]

    This can also be visualised as the list pivoting 90 degrees clockwise before flipping vertically.
    The reason for this complicated maneuver is so the point x = 0, y = 0 becomes the last value in
    the list so it is cast to the highest place on the screen.

    """
    map_width, map_height = len(value_map[0]), len(value_map)

    # Create the new list
    rotated_map = [[] for i in range(map_width)]
    for y in value_map:
        for index_x, x in enumerate(y):
            # Take the x values and insert them into the columns so the entire map becomes rotated.
            rotated_map[map_width-1-index_x].insert(0, x)

    """
    Debug loop
    
    for layer in rotated_map:
        print(layer)
    """
    return rotated_map


class MapHandler:

    def __init__(self):
        # Read the map. This will later be a list of maps depending on the area.
        self.map = arcade.read_tmx("tiled/tilemaps/mvp.tmx")

        # Save the layers for the map in a dictionary
        self.layers = None
        self.ground_layer = None
        self.load_map(self.map)

    def load_map(self, map_data):
        self.layers = {}
        for layer_num, layer_data in enumerate(map_data.layers):
            tile_list = isometric.IsoList()
            flipped_data = xy_rotate_map(layer_data.layer_data)

            for e_y, y in enumerate(flipped_data):
                for e_x, x in enumerate(y):
                    if x:
                        px, py, pz = isometric.cast_to_iso(e_x, e_y, flipped_data, tile_list)
                        tile = isometric.IsoSprite(e_x, e_y, px, py, pz, tiles.find_iso_data(x))
                        tile_list.append(tile)
            tile_list.reorder_isometric()
            self.layers[layer_data.name] = isometric.IsoLayer(layer_data, flipped_data, tile_list)
        self.ground_layer = self.layers['ground_layer'].map_data

    def apply_shown(self):
        all_tiles = isometric.IsoList()
        for layer in self.layers.values():
            if layer.shown:
                all_tiles.extend(layer.tiles)
        all_tiles.reorder_isometric()
        return all_tiles