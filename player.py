import time

import arcade

import isometric
import algorithms
import constants as c

PLAYER_ISO_DATA = isometric.generate_iso_data_other('player')[0]
SELECTED_ISO_DATA, SELECTED_ISO_CAP = isometric.generate_iso_data_other('selected')
HOVER_ISO_DATA, HOVER_ISO_CAP = isometric.generate_iso_data_other('select')

EDGES = {key: data for key, data in enumerate(isometric.generate_iso_data_other('caps'))}


class Player(isometric.IsoActor):

    def __init__(self, e_x, e_y, game_view):
        x, y, z = isometric.cast_to_iso(e_x, e_y)
        super().__init__(e_x, e_y, PLAYER_ISO_DATA)
        self.game_view = game_view
        self.walls = []
        self.path_finding_last = {'init': 0, 'pos': (0, 0)}
        self.set_grid(algorithms.PathFindingGrid(self.game_view.map_handler))

    def new_pos(self, e_x, e_y):
        super().new_pos(e_x, e_y)
        self.game_view.map_handler.run_display('player', self.e_x, self.e_y)

    def load_paths(self):
        if self.path_finding_last['init'] != self.action_handler.initiative or \
           self.path_finding_last['pos'] != (self.e_x, self.e_y):
            c.iso_strip(self.walls)
            super().load_paths()
            self.walls = []
            for node in self.path_finding_data[-1]:
                if self.path_finding_data[1][node] <= self.action_handler.initiative:
                    for index, neighbor in enumerate(node.directions):
                        if neighbor is None:
                            self.walls.append(isometric.IsoSprite(*node.location, EDGES[index]))
                else:
                    break

            for node in self.path_finding_data[2][self.action_handler.initiative]:
                for index, neighbor in enumerate(node.directions):
                    if neighbor is not None and self.path_finding_data[1][neighbor] > self.path_finding_data[1][node]:
                        self.walls.append(isometric.IsoSprite(*node.location, EDGES[index]))
            c.iso_extend(self.walls)
            self.path_finding_last = {'init': self.action_handler.initiative, 'pos': (self.e_x, self.e_y)}


class Select(isometric.IsoSprite):

    def __init__(self, e_x, e_y):
        super().__init__(e_x, e_y, HOVER_ISO_DATA)
        self.cap = isometric.IsoSprite(e_x, e_y, HOVER_ISO_CAP)
        c.iso_extend([self, self.cap])

    def new_pos(self, e_x, e_y):
        super().new_pos(e_x, e_y)
        self.cap.new_pos(e_x, e_y)


class Selected(isometric.IsoSprite):
    def __init__(self, e_x, e_y):
        super().__init__(e_x, e_y, SELECTED_ISO_DATA)
        self.cap = isometric.IsoSprite(e_x, e_y, SELECTED_ISO_CAP)
        c.iso_extend([self, self.cap])

    def new_pos(self, e_x, e_y):
        super().new_pos(e_x, e_y)
        self.cap.new_pos(e_x, e_y)