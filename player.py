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
        self.current_path = None

    def on_key_press(self, key):
        pass


class Select(isometric.IsoSprite):

    def __init__(self, e_x, e_y, e_map):
        x, y, z = isometric.cast_to_iso(e_x, e_y, e_map)
        super().__init__(e_x, e_y, x, y, z, HOVER_ISO_DATA)


class Selected(isometric.IsoSprite):
    def __init__(self, e_x, e_y, e_map):
        x, y, z = isometric.cast_to_iso(e_x, e_y, e_map)
        super().__init__(e_x, e_y, x, y, z, SELECTED_ISO_DATA)
