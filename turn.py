import time

import arcade

import algorithms
import isometric
import constants as c


class Action:
    def __init__(self, inputs, handler):
        self.end = False
        self.inputs = inputs
        self.handler = handler
        self.actor = handler.actor
        self.data = []
        self.cost = 0
        self.setup()

    def setup(self):
        self.find_cost()

    def begin(self):
        pass

    def find_cost(self):
        pass

    def update(self):
        return True

    def final(self):
        pass

    def draw(self):
        pass


class MoveAction(Action):

    def setup(self):
        self.handler.actor.load_paths()
        path = algorithms.reconstruct_path(self.actor.path_finding_grid,
                                           self.actor.path_finding_data[0],
                                           (self.actor.e_y, self.actor.e_x),
                                           (self.inputs[0].e_y, self.inputs[0].e_x))[:self.handler.initiative]

        if len(path):
            avg_x, avg_y = 0, 0
            for node in path:
                e_x, e_y = node.location
                x, y, z = isometric.cast_to_iso(e_x, e_y)
                avg_x += x
                avg_y += y
            self.handler.turn_handler.game_view.target_view_x = c.round_to_x(avg_x / len(path) - c.SCREEN_WIDTH / 2,
                                                                             5 * c.SPRITE_SCALE)
            self.handler.turn_handler.game_view.target_view_y = c.round_to_x(avg_y / len(path) - c.SCREEN_HEIGHT / 2,
                                                                             5 * c.SPRITE_SCALE)
        self.data.append(path)
        self.find_cost()

    def begin(self):
        pass

    def find_cost(self):
        if len(self.data[0]):
            node = self.data[0][-1]
            self.cost = self.actor.path_finding_data[1][node]
        else:
            self.cost = 0

    def update(self):
        if len(self.data[0]):
            next_node = self.data[0].pop(0)
            self.actor.new_pos(*next_node.location)
            return False
        return True

    def final(self):
        self.actor.load_paths()

    def draw(self):
        start = self.actor.e_x, self.actor.e_y
        for node in self.data[0]:
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
        self.data.append(self.handler.turn_handler.game_view.tabs[1])
        self.data[0].load_convo(self.inputs[0].interaction_data)

    def update(self):
        return self.data[0].convo_done


class ShootAction(Action):
    def update(self):
        return True


ACTIONS = {"move": MoveAction, "hold": HoldAction, "dash": DashAction, 'interact': InteractAction, 'shoot': ShootAction}


class ActionHandler:
    def __init__(self, actor, base=10):
        self._pending_action: Action = None
        self._current_action: Action = None
        self.actor = actor
        self.base_initiative = base
        self.initiative = base
        self.pending_initiative = base
        self.next_initiative = base
        self.turn_handler = None

    def complete(self):
        self.current_action = None
        self._pending_action = None
        self.initiative = self.next_initiative
        self.pending_initiative = self.initiative
        self.next_initiative = self.base_initiative

    def on_update(self, delta_time: float = 1/60):
        if self.current_action is not None and self.current_action.update():
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
        self.action_handlers: list[ActionHandler] = sorted(action_handlers, key=lambda handlers: handlers.initiative)
        self.complete: list[ActionHandler] = []
        self.current_handler: ActionHandler = None
        self.game_view = game_view
        self.update_timer = 0

    def new_action_handlers(self, new_handlers):
        self.complete.extend(new_handlers)

    def cycle(self):
        self.update_timer = time.time()
        if self.current_handler is not None:
            self.complete.append(self.current_handler)
            self.current_handler.complete()
        if len(self.action_handlers):
            self.current_handler = self.action_handlers.pop(0)
            if self.current_handler.turn_handler is None:
                self.current_handler.turn_handler = self
        else:
            self.action_handlers = sorted(self.complete, key=lambda handlers: handlers.initiative)
            self.complete = []
            self.current_handler = self.action_handlers.pop(0)
            if self.current_handler.turn_handler is None:
                self.current_handler.turn_handler = self

    def on_update(self, delta_time: float = 1/60):
        if self.current_handler is None:
            self.cycle()
        elif time.time() > self.update_timer + 1/6:
            self.update_timer = time.time()
            if self.current_handler.on_update(delta_time):
                self.cycle()

    def on_draw(self):
        if self.current_handler is not None:
            self.current_handler.draw()
            arcade.draw_text(f"actor: {self.current_handler.actor},\n"
                             f"initiative: {self.current_handler.initiative},\n"
                             f"pending initiative: {self.current_handler.pending_initiative}",
                             0, 0, arcade.color.RADICAL_RED)
