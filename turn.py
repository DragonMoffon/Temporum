import time

import arcade

import isometric
import algorithms


class ActionHandler:

    def __init__(self, actor):
        self.actor = actor
        try:
            actor.action_handler = self
        finally:
            self.initiative = 0
            self.initiative_cost = 10
            self.actions = []
            self.done_actions = []
            self.current_action = None

    def reset_turn(self):
        self.current_action = None
        self.done_actions = []
        self.initiative = 0
        self.initiative += self.initiative_cost
        self.initiative_cost = 10

    def next(self):
        self.current_action = self.actions.pop(0)
        if self.current_action.on_act():
            self.current_action = None
            return True
        else:
            self.initiative_cost -= self.current_action.cost
            return False

    def update(self):
        if self.current_action is not None:
            if self.current_action.update(self.actor):
                self.done_actions.append(self.current_action)
                if self.initiative_cost <= 0:
                    return True
                elif len(self.actions):
                    return self.next()
            return False
        else:
            if self.initiative_cost <= 0:
                return True
            elif len(self.actions):
                return self.next()
            return False

    def calculate_remaining(self):
        cost = 0
        for action in self.actions:
            cost += action.cost

        return self.initiative_cost - cost

    def draw(self):
        if self.current_action is not None:
            self.current_action.draw()


class TurnHandler:

    def __init__(self, window, player, non_player_actors):
        self.window = window
        self.actors = [player]
        self.actors.extend(non_player_actors)
        self.action_handlers = {ActionHandler(actor): actor for actor in self.actors}
        self.ordered_actors = []
        self.order_actors()
        self.current_actor = self.ordered_actors[0]
        self.turn_timer = 0
        self.turns = []

    def order_actors(self):
        self.ordered_actors = sorted(self.action_handlers.keys(), reverse=True,
                                     key=lambda handlers: handlers.initiative)
        self.ordered_actors.append(None)

    def end_turn(self):
        self.turns.append(Turn(self.ordered_actors))
        for actors in self.ordered_actors[:-1]:
            actors.reset_turn()
        self.order_actors()
        self.current_actor = self.ordered_actors[0]
        self.turn_timer = time.time()

    def update(self):
        if self.current_actor is None:
            self.end_turn()
        else:
            if not self.turn_timer:
                self.turn_timer = time.time()
            elif time.time() >= self.turn_timer + 1/6:
                self.turn_timer = time.time()
                if self.current_actor.update():
                    self.push_to_next_actor()

    def push_to_next_actor(self):
        self.current_actor = self.ordered_actors[self.ordered_actors.index(self.current_actor) + 1]
        self.turn_timer = time.time()

    def draw(self):
        if self.current_actor is not None:
            self.current_actor.draw()
            arcade.draw_text(f"{self.current_actor.actor}, {self.current_actor.initiative_cost}",
                             0, 0, arcade.color.WHITE)
        else:
            arcade.draw_text(str(self.current_actor),
                             0, 0, arcade.color.WHITE)


class Turn:

    def __init__(self, ordered_actors):
        self.ordered_actors = ordered_actors[:-1]
        self.ordered_actions = {actor: actor.done_actions for actor in ordered_actors[:-1]}


class Action:

    def __init__(self, cost):
        self.cost = cost

    def on_act(self):
        pass

    def update(self, actor):
        pass

    def draw(self):
        pass


class End(Action):

    def __init__(self):
        super().__init__(0)

    def on_act(self):
        return True


class Move(Action):

    def __init__(self, path):
        super().__init__(len(path))
        self.path = path + [None]
        self.current_node = None

    def on_act(self):
        if len(self.path):
            self.current_node = self.path.pop(0)
            return False
        return True

    def update(self, actor: isometric.IsoSprite):
        if self.current_node is not None:
            actor.new_pos(self.current_node.location[0], self.current_node.location[1])
            if len(self.path):
                self.current_node = self.path.pop(0)
            return False
        return True
