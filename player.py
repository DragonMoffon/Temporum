
import arcade

import turn
import isometric
import algorithms
import constants as c

PLAYER_ISO_DATA = isometric.IsoTexture("assets/iso_player_character.png", .0, 45.0, 0, 0, 160, 320)
SELECTED_ISO_DATA = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 0, 0, 160, 320)
HOVER_ISO_DATA = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 160, 0, 160, 320)


class Player(isometric.IsoSprite):

    def __init__(self, e_x, e_y, e_map, game_view):
        x, y, z = isometric.cast_to_iso(e_x, e_y, (len(e_map), len(e_map[0])), z_mod=0.5)
        super().__init__(e_x, e_y, x, y, z, PLAYER_ISO_DATA, z_mod=0.5)
        self.ground_map = e_map
        self.game_view = game_view
        self.walls = game_view.map_handler.layers['wall_layer'].tile_map
        self.current_path = None
        self.check_path = None
        self.action_handler: turn.ActionHandler = None

    def on_key_press(self, key, shift):
        if self.current_path is not None and key == arcade.key.ENTER:
            self.move()

    def act(self, action_handler):
        if self.action_handler is None or action_handler != self.action_handler:
            self.action_handler = action_handler

        if self.action_handler is not None:
            if not self.action_handler.calculate_remaining():
                self.action_handler.actions.append(turn.End())

    def find_move(self, selected_tile, shift):
        if shift and self.current_path is not None:
            location = self.current_path[-1].location
            self.check_path = algorithms.path_2d(self.game_view.map_handler.path_finding_map,
                                                 (location[1], location[0]),
                                                 (selected_tile.e_y, selected_tile.e_x))
        else:
            self.check_path = algorithms.path_2d(self.game_view.map_handler.path_finding_map,
                                                 (self.e_y, self.e_x),
                                                 (selected_tile.e_y, selected_tile.e_x))

    def set_move(self, shift):
        if self.current_path is not None and shift:
            self.current_path += self.check_path[:self.action_handler.calculate_remaining()-len(self.current_path)]
        else:
            self.current_path = self.check_path[:self.action_handler.calculate_remaining()]

    def move(self):
        if len(self.current_path):
            path = self.current_path
            self.current_path = None
            self.action_handler.actions.append(turn.Move(path))


class Select(isometric.IsoSprite):

    def __init__(self, e_x, e_y, z_mod, map_size):
        x, y, z = isometric.cast_to_iso(e_x, e_y, map_size)
        super().__init__(e_x, e_y, x, y, z, HOVER_ISO_DATA, z_mod)


class Selected(isometric.IsoSprite):
    def __init__(self, e_x, e_y, z_mod, map_size):
        x, y, z = isometric.cast_to_iso(e_x, e_y, map_size, z_mod)
        super().__init__(e_x, e_y, x, y, z, SELECTED_ISO_DATA)
