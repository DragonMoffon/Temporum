class TurnManager:
    """
    The turn manager is created by the game object and manages all of the turns and super positions.
    """
    def __init__(self):
        pass


class Actor:
    """
    Every Character be it the player or an enemy that takes an action each turn creates an Actor class with their
    initiative and other data like their speed, and action number cap.
    """
    def __init__(self, creator):
        self.character = creator
        self.max_move = 0
        self.initiative = 0


class SuperPosition:
    """
    A super position holds all of the Turn objects for that super position. A new SuperPosition object is created
    every time the player time loops.
    """

    def __init__(self):
        pass


class Turn:
    """
    A Turn object is made for every turn and each superposition has its turns recorded.

    """
    def __init__(self, acting_characters):
        self.acting_characters = acting_characters
        self.actions = {i.initiative: [] for i in acting_characters}


class Action:
    """
    An Actor can only call a certain number of objects. all actions that a character can take are children of the base
    Action Class. This holds the data like the Action Value, Included Actors, and Allowed Actors.
    """
    def __init__(self, a_value):
        self.action_value = a_value
        self.incl_actors = {}
        self.allow_actor = {}


class Move(Action):
    """
    Move is the simplest Action that any Actor can take. It simply moves them a set number of times. Moving a single
    tile uses one action point. each character has a set number each turn.
    """
    def __init__(self):
        super().__init__(1)
