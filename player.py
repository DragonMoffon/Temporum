import arcade
import isometric
import constants as c

PLAYER_ISO_DATA = isometric.IsoTexture("assets/iso_player_character.png", .0, 45.0, 0, 0, 160, 320)
SELECTED_ISO_DATA = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 0, 0, 160, 320)
HOVER_ISO_DATA = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 160, 0, 160, 320)


class Player(isometric.IsoSprite):

    def __init__(self, e_x, e_y, e_map, game_view):
        x, y, z = isometric.cast_to_iso(e_x, e_y, e_map, z_mod=0.5)
        super().__init__(e_x, e_y, x, y, z, PLAYER_ISO_DATA)
        self.ground_map = e_map
        self.game_view = game_view
        self.walls = game_view.map_handler.layers['wall_layer'].tile_map

    def on_key_press(self, key):
        if key in c.DIRECTIONS:
            direction = c.DIRECTIONS[key]
            direction_inv = (direction + 2) % 4
            n_x = self.e_x
            n_y = self.e_y
            iso_current = self.walls[n_x, n_y]
            if key == arcade.key.UP:
                n_y -= 1
            elif key == arcade.key.DOWN:
                n_y += 1
            elif key == arcade.key.LEFT:
                n_x -= 1
            elif key == arcade.key.RIGHT:
                n_x += 1
            iso_check = self.walls[n_x, n_y]
            if self.ground_map[n_y][n_x]:
                if iso_current is None or iso_current is not None and iso_current.iso_data['directions'][direction_inv]:
                    if iso_check is None or iso_check is not None and iso_check.iso_data['directions'][direction]:
                        self.new_pos(n_x, n_y, self.ground_map, self.game_view.shown_tiles, .5)


class Select(isometric.IsoSprite):

    def __init__(self, e_x, e_y, e_map):
        x, y, z = isometric.cast_to_iso(e_x, e_y, e_map)
        super().__init__(e_x, e_y, x, y, z, HOVER_ISO_DATA)


class Selected(isometric.IsoSprite):
    def __init__(self, e_x, e_y, e_map):
        x, y, z = isometric.cast_to_iso(e_x, e_y, e_map)
        super().__init__(e_x, e_y, x, y, z, SELECTED_ISO_DATA)
