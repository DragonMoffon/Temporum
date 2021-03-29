import arcade


def xy_rotate_map(value_map):
    """
    :param value_map: The 2D array which holds the data to be rotated
    :return: It returns the rotated map. The X rows become the Y columns and vice-versa
    """
    map_width, map_height = len(value_map[0]), len(value_map)

    # Create the new list
    rotated_map = [[] for i in range(map_width)]
    for y in value_map:
        for index_x, x in enumerate(y):
            # Take the x values and insert them into the columns so the entire map becomes rotated.
            rotated_map[map_width-1-index_x].insert(0, x)

    return rotated_map


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
        self.sprite_list = sorted(self.sprite_list, key=lambda tile: tile.z)

        for idx, sprite in enumerate(self.sprite_list):
            self.sprite_idx[sprite] = idx

        self._vao1 = None
