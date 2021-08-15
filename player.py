import isometric
import constants as c

PLAYER_ISO_DATA = isometric.generate_iso_data_other('player')[0]
SELECTED_ISO_DATA, SELECTED_ISO_CAP = isometric.generate_iso_data_other('selected')
HOVER_ISO_DATA, HOVER_ISO_CAP = isometric.generate_iso_data_other('select')

EDGES = {key: data for key, data in enumerate(isometric.generate_iso_data_other('caps'))}


class Player(isometric.IsoActor):

    def __init__(self, e_x, e_y, game_view):
        super().__init__(e_x, e_y, PLAYER_ISO_DATA)
        self.game_view = game_view
        self.walls = []
        self.path_finding_last = {'init': -1, 'pos': (-1, -1)}
        self.animations = {
            'idle': isometric.IsoAnimation("assets/characters/Iso_Idle.png", (160, 320), (0, 0), 15, 1/12)
        }
        self.current_animation = None

    def new_pos(self, e_x, e_y):
        """
        new pos sets the x and y position of the player based on a e_x and e_y value. it also runs the display system
        from the map handler.
        :param e_x: the new euclidean x position
        :param e_y: the new euclidean y position
        """
        super().new_pos(e_x, e_y)
        self.game_view.map_handler.map.vision_handler.recalculate = True
        self.set_edges_short()

    def new_map_pos(self, e_x, e_y):
        super().new_map_pos(e_x, e_y)
        self.game_view.map_handler.map.vision_handler.recalculate = True
        self.set_edges_short()

    def set_edges_short(self):
        c.iso_strip(self.walls)
        self.walls = []
        for index in range(4):
            self.walls.append(isometric.IsoSprite(self.e_x, self.e_y, EDGES[index]))
        c.iso_extend(self.walls)

    def load_paths(self, algorithm='base'):
        if self.action_handler.initiative >= 0:
            if self.path_finding_last['init'] != self.action_handler.initiative or \
               self.path_finding_last['pos'] != (self.e_x, self.e_y) or \
               self.game_view.map_handler.map.changed:
                self.game_view.map_handler.map.changed = False
                super().load_paths()
                self.gen_walls()
                self.path_finding_last = {'init': self.action_handler.initiative, 'pos': (self.e_x, self.e_y)}

    def gen_walls(self):
        c.iso_strip(self.walls)
        self.walls = []

        for node in self.path_finding_data[-1]:
            if (self.game_view.map_handler.map.vision_handler.vision_image is not None and
                    self.game_view.map_handler.map.vision_handler.vision_image.getpixel(node.location)[0]):
                if self.path_finding_data[1][node] <= self.action_handler.initiative:
                    for index, neighbor in enumerate(node.neighbours):
                        neighbor_to_node = (index + 2) % 4
                        if neighbor is None:
                            self.walls.append(isometric.IsoSprite(*node.location, EDGES[index]))
                        elif not node.directions[index] or not neighbor.directions[neighbor_to_node] or \
                                neighbor not in self.path_finding_data[1]:
                            self.walls.append(isometric.IsoSprite(*node.location, EDGES[index]))
                else:
                    break

        c.iso_extend(self.walls)

    def update_animation(self, delta_time: float = 1/60):
        if self.current_animation is None and self.action_handler is not self.game_view.turn_handler.current_handler:
            self.current_animation = self.animations['idle']
        elif self.current_animation is not None:
            next_frame = self.current_animation.update_animation(delta_time)
            if next_frame is not None:
                self.texture = next_frame
            else:
                self.texture = self.base
                self.current_animation = None


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
