import math
import random
import time

import arcade
from typing import List

import algorithms
import isometric
import constants as c


class Action:
    def __init__(self, inputs, handler):
        self.end = False
        self.inputs = inputs
        self.handler = handler
        self.actor = handler.actor
        self.data = {}
        self.cost = 0
        self.setup()

        self.turn_timer = 0

    def setup(self):
        self.find_cost()

    def begin(self):
        pass

    def find_cost(self):
        self.cost = 1

    def update(self):
        return True

    def on_update(self, delta_time: float = 1/60):
        self.turn_timer += delta_time
        if self.turn_timer > 1/8:
            self.turn_timer -= 1/8
            return self.update()
        return False

    def final(self):
        pass

    def draw(self):
        pass

    def can_complete(self):
        if self.cost <= self.handler.initiative:
            return True
        return False

    def done_animating(self):
        pass


class MoveAction(Action):

    def setup(self):
        self.handler.actor.load_paths()
        path = algorithms.reconstruct_path(self.actor.path_finding_grid,
                                           self.actor.path_finding_data[0],
                                           (self.actor.e_x, self.actor.e_y),
                                           (self.inputs[0].e_x, self.inputs[0].e_y))[:self.handler.initiative]
        self.data['path'] = path
        self.find_cost()

    def can_complete(self):
        if len(self.data['path']):
            return True
        return False

    def begin(self):
        if len(self.data['path']):
            all_points = tuple(zip(*tuple(map(lambda point: point.location, self.data['path']))))
            avg_x, avg_y = sum(all_points[0]), sum(all_points[1])
            x, y, z = isometric.cast_to_iso(avg_x/len(self.data['path']), avg_y/len(self.data['path']))
            self.handler.turn_handler.game_view.pending_motion.append((x-c.SCREEN_WIDTH//2,
                                                                       y-c.SCREEN_HEIGHT//2))

    def find_cost(self):
        self.cost = len(self.data['path'])

    def update(self):
        if len(self.data['path']):
            next_node = self.data['path'].pop(0)
            self.actor.new_pos(*next_node.location)
            return False
        return True

    def final(self):
        self.actor.load_paths()

    def draw(self):
        start = self.actor.e_x, self.actor.e_y
        for node in self.data['path']:
            end = node.location
            end_x, end_y, end_z = isometric.cast_to_iso(end[0], end[1])
            start_x, start_y, start_z = isometric.cast_to_iso(start[0], start[1])
            arcade.draw_line(start_x, start_y-55, end_x, end_y-55, arcade.color.ELECTRIC_BLUE, 2)
            start = end


class MoveEAction(Action):
    def setup(self):
        target = (c.clamp(c.PLAYER.e_x + random.choice((-2, -1, 1, 2)), 0, c.CURRENT_MAP_SIZE[0]-1),
                  c.clamp(c.PLAYER.e_y + random.choice((-2, -1, 1, -2)), 0, c.CURRENT_MAP_SIZE[1]-1))
        self.actor.load_paths()
        came_from = self.actor.path_finding_data[0]

        if target in self.actor.path_finding_grid and self.actor.path_finding_grid[target] in came_from:
            end = target
        else:
            goal = self.actor.path_finding_data[-1].get()
            end = goal.location

        if end == (self.actor.e_x, self.actor.e_y):
            path = []
        else:
            path = algorithms.reconstruct_path(self.actor.path_finding_grid, came_from,
                                               (self.actor.e_x, self.actor.e_y), end)

        self.data['path'] = path
        self.find_cost()

    def begin(self):
        if len(self.data['path']) and self.actor in c.ISO_LIST:
            all_points = tuple(zip(*tuple(map(lambda point: point.location, self.data['path']))))
            avg_x, avg_y = sum(all_points[0]), sum(all_points[1])
            x, y, z = isometric.cast_to_iso(avg_x/len(self.data['path']), avg_y/len(self.data['path']))
            self.handler.turn_handler.game_view.pending_motion.append((x-c.SCREEN_WIDTH//2,
                                                                       y-c.SCREEN_HEIGHT//2))
        elif not len(self.data['path']):
            self.actor.end_turn = True

    def find_cost(self):
        self.cost = len(self.data['path'])

    def update(self):
        if len(self.data['path']):
            next_node = self.data['path'].pop(0)
            self.actor.new_pos(*next_node.location)
            return False
        return True

    def draw(self):
        start = self.actor.e_x, self.actor.e_y
        for node in self.data['path']:
            end = node.location
            end_x, end_y, end_z = isometric.cast_to_iso(end[0], end[1])
            start_x, start_y, start_z = isometric.cast_to_iso(start[0], start[1])
            arcade.draw_line(start_x, start_y-55, end_x, end_y-55, arcade.color.ELECTRIC_BLUE, 2)
            start = end


class HoldAction(Action):
    def find_cost(self):
        self.cost = self.handler.initiative

    def begin(self):
        if self.cost > self.handler.base_initiative:
            self.handler.next_initiative += self.handler.base_initiative//2
        else:
            self.handler.next_initiative += self.cost//2

    def update(self):
        return True


class DashAction(Action):
    def find_cost(self):
        self.cost = self.handler.initiative

    def begin(self):
        if self.cost > self.handler.base_initiative:
            self.handler.next_initiative -= self.handler.base_initiative//2
        else:
            self.handler.next_initiative -= self.cost//2

    def update(self):
        return True


class InteractAction(Action):

    def begin(self):
        self.data['interact'] = self.handler.turn_handler.game_view.tabs[0]
        self.data['interact'].load_convo(self.inputs[0].interaction_data)

    def update(self):
        return self.data['interact'].convo_done

    def can_complete(self):
        if (self.cost <= self.handler.initiative and
                abs(self.inputs[0].e_x-self.actor.e_x) <= 1 and abs(self.inputs[0].e_y-self.actor.e_y) <= 1):
            return True
        return False


class LeaveAction(Action):
    def find_cost(self):
        self.cost = 0

    def can_complete(self):
        if self.inputs[0].e_x == self.actor.e_x and self.inputs[0].e_y == self.actor.e_y:
            return True
        return False

    def update(self):
        self.handler.turn_handler.game_view.map_handler.use_gate(self.inputs[0].gate_data)
        return True


class ShootAction(Action):
    def setup(self):
        self.find_cost()
        start_point = self.actor.e_x, self.actor.e_y
        target_point = self.inputs[0].e_x, self.inputs[0].e_y

        d_pos = target_point[0] - start_point[0], target_point[1] - start_point[1]
        self.data['abs_pos'] = abs(d_pos[0]), abs(d_pos[1])
        if d_pos[0]:
            self.data['facing'] = 0 if d_pos[0] > 0 else 1
        else:
            self.data['facing'] = 0 if d_pos[1] < 0 else 1

        self.data['iters'] = [0, 0]
        self.data['bullet_pos'] = list(start_point)
        self.data['last'] = list(start_point)

        self.data['length'] = max(self.data['abs_pos'])
        self.data['step'] = 0

    def find_cost(self):
        self.cost = int(5 + c.floor_to_x(math.sqrt((self.actor.e_x-self.inputs[0].e_x)**2 +
                                                   (self.actor.e_y-self.inputs[0].e_y)**2), 10)/2)

    def can_complete(self):
        if (self.actor not in self.inputs and self.cost <= self.handler.initiative and
               (self.actor.e_x != self.inputs[0].e_x or self.actor.e_y != self.inputs[0].e_y) and
                self.handler.turn_handler.game_view.map_handler.map.vision_handler.
                        vision_image.getpixel((self.actor.e_x, self.actor.e_y))[0]):
            return True
        return False

    def begin(self):
        self.actor.add_animation('fire', self, self.data['facing'])

    def on_update(self, delta_time: float = 1/60):
        return self.update()

    def update(self):
        def lerp(normal):
            lerp_x = self.actor.e_x + (self.inputs[0].e_x-self.actor.e_x) * normal
            lerp_y = self.actor.e_y + (self.inputs[0].e_y-self.actor.e_y) * normal
            return lerp_x, lerp_y

        if 'bullet' in self.data:
            if self.data['step'] <= self.data['length']:
                bullet = self.data['bullet']
                t = self.data['step']/self.data['length'] if self.data['step'] else 0.0
                bullet.new_pos(*lerp(t))
                self.data['step'] += 1
                return False

            if isinstance(self.inputs[0], isometric.IsoActor):
                self.inputs[0].hit(self.actor)
            else:
                self.inputs[0].push_animation('hit', None, 1-self.data['facing'])
            c.iso_remove(self.data['bullet'])
            return True
        return False

    def draw(self):
        if 'bullet' in self.data:
            e_x = round(self.data['bullet'].e_x)
            e_y = round(self.data['bullet'].e_y)
            x, y, z = isometric.cast_to_iso(e_x, e_y)
            arcade.draw_point(x, y-60, arcade.color.RADICAL_RED, 6)

    def done_animating(self):
        if 'bullet' not in self.data:
            # If the bullet has not been made yet then only the firing animation has played. Time to make bullet and
            # play recoil animation.
            bullet_iso_data = isometric.IsoData(arcade.load_texture("assets/characters/player_bullet.png",
                                                                    width=160, height=10),
                                                None)
            self.data['bullet'] = isometric.IsoSprite(self.actor.e_x, self.actor.e_y, bullet_iso_data)

            # Find the isometric angle between the shooter and the target. This is the bullet's angle.
            iso_x_diff = (self.inputs[0].e_x - self.inputs[0].e_y) - (self.actor.e_x - self.actor.e_y)
            iso_y_diff = 0.5 * (-(self.inputs[0].e_x + self.inputs[0].e_y) + (self.actor.e_x + self.actor.e_y))
            angle = math.atan2(iso_y_diff, iso_x_diff)
            self.data['bullet'].radians = angle

            c.iso_append(self.data['bullet'])

            self.actor.push_animation('recoil', None, self.data['facing'])


ACTIONS = {"move": MoveAction, "end": HoldAction, "dash": DashAction,
           'interact': InteractAction, 'shoot': ShootAction, 'move_enemy': MoveEAction,
           "leave": LeaveAction}


class ActionHandler:
    def __init__(self, actor, base=10):
        self._pending_action: Action = None
        self._current_action: Action = None
        self.actor = actor
        self.base_initiative = base
        self._initiative = base
        self.pending_initiative = base
        self.next_initiative = base
        self.turn_handler = None

    def pass_turn(self):
        self.turn_handler.cycle()

    def complete(self):
        self.current_action = None
        self._pending_action = None
        self.initiative = self.next_initiative
        self.pending_initiative = self.initiative
        self.next_initiative = self.base_initiative

    def on_update(self, delta_time: float = 1/60):
        if self.current_action is not None and self.current_action.on_update(delta_time):
            self.current_action.final()
            self.current_action = None
        elif self.initiative <= 0 and self.current_action is None:
            return True
        return False

    def draw(self):
        if self.pending_action is not None:
            self.pending_action.draw()

        if self.current_action is not None:
            self.current_action.draw()

    @property
    def initiative(self):
        return self._initiative

    @initiative.setter
    def initiative(self, value):
        self._initiative = value
        if self.turn_handler is not None and self.turn_handler.current_handler == self:
            self.actor.load_paths()

    @property
    def pending_action(self):
        return self._pending_action

    @pending_action.setter
    def pending_action(self, value):
        if value is not None:
            new_initiative = self.initiative - value.cost
            if new_initiative >= 0:
                self._pending_action = value
                self.pending_initiative = new_initiative
            else:
                self._pending_action = None
                self.pending_initiative = self.initiative
        else:
            self._pending_action = value
            self.pending_initiative = self.initiative

    @property
    def current_action(self):
        return self._current_action

    @current_action.setter
    def current_action(self, value):
        if value is not None:
            self.initiative -= value.cost
        self._current_action = value
        self.pending_action = None
        if self.current_action is not None:
            self.current_action.begin()


class TurnHandler:
    def __init__(self, action_handlers: list, game_view):
        self.action_handlers: List[ActionHandler] = sorted(action_handlers, key=lambda handlers: handlers.initiative)
        self.complete: List[ActionHandler] = []
        self.current_handler: ActionHandler = None
        self.game_view = game_view
        self.update_timer = 0

    def new_action_handlers(self, new_handlers):
        self.complete.extend(new_handlers)

    def reset_action_handlers(self, new_handlers):
        self.action_handlers: List[ActionHandler] = sorted(new_handlers, key=lambda handlers: handlers.initiative)
        self.current_handler: List[ActionHandler] = []
        self.current_handler = None
        self.update_timer = 0

    def remove_action_handlers(self, removed_handlers):
        for handler in removed_handlers:
            if handler in self.action_handlers:
                self.action_handlers.remove(handler)
            elif handler in self.complete:
                self.complete.remove(handler)

        if self.current_handler in removed_handlers:
            handler = self.current_handler
            self.cycle()
            self.complete.remove(handler)

    def next_actor(self):
        self.current_handler = self.action_handlers.pop(0)
        if self.current_handler.turn_handler is None:
            self.current_handler.turn_handler = self

        self.current_handler.actor.load_paths()

        if self.current_handler == self.game_view.player.action_handler:
            self.game_view.player.gen_walls()
            self.game_view.pending_motion.append((self.current_handler.actor.center_x - c.SCREEN_WIDTH//2,
                                                  self.current_handler.actor.center_y - c.SCREEN_HEIGHT//2))

    def cycle(self):
        self.update_timer = time.time()
        last = None
        if self.current_handler is not None:
            self.complete.append(self.current_handler)
            last = self.current_handler
        if len(self.action_handlers):
            self.next_actor()
        else:
            self.action_handlers = sorted(self.complete, key=lambda handlers: handlers.next_initiative)
            self.complete = []
            self.next_actor()

        if last is not None:
            last.complete()

    def on_update(self, delta_time: float = 1/60):
        if self.current_handler is None:
            self.cycle()
        elif self.current_handler.on_update(delta_time):
            self.cycle()

    def on_draw(self):
        if self.current_handler is not None and self.current_handler.actor in c.ISO_LIST:
            self.current_handler.draw()
