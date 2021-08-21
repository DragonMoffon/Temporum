import random

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
            'idle': isometric.IsoAnimation("assets/characters/Iso_Idle.png", (320, 320), (0, 0), 15, 1/12),
            'fire': isometric.IsoAnimation("assets/characters/Iso_Idle.png", (320, 320), (0, 640), 6, 1/12),
            'recoil': isometric.IsoAnimation("assets/characters/Iso_Idle.png", (320, 320), (0, 960), 8, 1/12),
            'hit': isometric.IsoAnimation("assets/characters/Iso_Idle.png", (320, 320), (0, 1280), 6, 1/12)
        }
        self.current_animation = None
        self.wait_time = 0.0
        self.idle_timer = 0.0

        self.current_trigger = None

        self.pending_animations = []

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
        """
        Every update this runs. The basic system is that every update it either animates, finds the next animation, or
        checks to see if the idle should run.
        :param delta_time: the difference between two frames in seconds. used to count how long an animation needs to
        run for.
        """

        # When not animating the player waits a little amount before doing an idle animation.
        if self.wait_time:
            self.idle_timer += delta_time

        if self.current_animation is not None:
            # If there is a current animation find the next frame.
            next_frame = self.current_animation.update_animation(delta_time)

            # if the animation is finished then the frame is none, else its the next texture needed.
            if next_frame is not None:
                self.texture = next_frame
            else:
                # If the animation was triggered by something we need to tell the trigger that it is done.
                if self.current_trigger is not None:
                    self.current_trigger.done_animating()
                    self.current_trigger = None

                # Add the wait time and reset timer.
                self.wait_time = random.uniform(2 / 60, 2 / 5)
                self.idle_timer = 0.0

                # if there are pending animations we want to start animating them.
                self.texture = self.base
                self.current_animation = None

                if len(self.pending_animations):
                    # Loop until we find the next valid animation. This is to protect against using the wrong key in a
                    # dict. Most of the time it will run once.
                    while len(self.pending_animations) and self.current_animation is None:
                        next_animation, next_trigger, facing = self.pending_animations.pop(0)
                        if next_animation in self.animations:
                            self.current_animation = self.animations[next_animation]
                            self.current_animation.facing = facing
                            self.current_trigger = next_trigger
                            self.wait_time, self.idle_timer = 0.0, 0.0
                            self.texture = self.current_animation.start_animation()
                        else:
                            next_animation.done_animating()

        elif len(self.pending_animations):
            # If there is no animation but there are some pending, find the next one.
            while len(self.pending_animations) and self.current_animation is None:
                next_animation, next_trigger, facing = self.pending_animations.pop(0)
                if next_animation in self.animations:
                    self.current_animation = self.animations[next_animation]
                    self.current_animation.facing = facing
                    self.current_trigger = next_trigger
                    self.wait_time, self.idle_timer = 0.0, 0.0
                    self.texture = self.current_animation.start_animation()
                else:
                    next_animation.done_animating()
        elif (self.action_handler is not self.game_view.turn_handler.current_handler and
                self.idle_timer >= self.wait_time):
            # There are no animations and the wait time is over. Start doing the idle.
            self.wait_time, self.idle_timer = 0.0, 0.0
            self.current_trigger = None
            self.current_animation = self.animations['idle']
            self.texture = self.current_animation.start_animation()


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
