import isometric

from typing import Tuple, List, Dict


class Tile:
    """
    The tile holds all iso pieces(sprites) that hold the same e_x and e_y.
     It these to:
        calculate the vision and movement directions possible from this tile.
        record all possible actions and link them to specific tiles.
    """
    def __init__(self, pos: Tuple[int, int], tile_map):
        self.vision_handler = tile_map.vision_handler
        self.map = tile_map
        self.seen = False

        self.pieces: List[isometric.IsoSprite] = []
        self.actors: List[isometric.IsoActor] = []
        self.directions = [1, 1, 1, 1]
        self.vision = [1, 1, 1, 1]
        self.neighbours: List[Tile, Tile, Tile, Tile] = [None, None, None, None]
        self.location: Tuple[int, int] = pos
        self.available_actions: Dict[str, list] = {}

    def light_add(self, other):
        if other not in self.actors:
            self.actors.append(other)

            for action in other.actions:
                if action not in self.available_actions:
                    self.available_actions[action] = [other]
                else:
                    self.available_actions[action].append(other)

    def light_remove(self, other):
        if other in self.actors:
            self.actors.append(other)

            for action in other.actions:
                if action in self.available_actions and other in self.available_actions[action]:
                    self.available_actions[action].remove(other)
                    if not len(self.available_actions[action]):
                        self.available_actions.pop(action)

    def update(self, other):
        """
        this updates the directions, and the available actions of the tile.
        :param other: A IsoSprite that should be in the tile.
        """

        if other not in self.pieces:
            self.pieces.append(other)

        self.find_direction_vision()

        actions = list(set(self.available_actions.keys()) | set(other.actions))
        for action in actions:
            if action not in self.available_actions:
                self.available_actions[action] = [other]
            elif other not in self.available_actions[action]:
                self.available_actions[action].append(other)
            elif other in self.available_actions[action] and action not in other.actions:
                self.available_actions[action].remove(other)

        self.map.changed = True

    def mix_directions(self, other):
        self.directions = [dirs*other[index] for index, dirs in enumerate(self.directions)]

    def mix_vision(self, other):
        self.vision = [vision*other[index] for index, vision in enumerate(self.vision)]
        self.vision_handler.modify_map(self.location, self.vision)

    def solve_direction(self, index):
        for piece in self.pieces:
            if not piece.direction[index]:
                return False
        return True

    def solve_vision(self, index):
        for piece in self.pieces:
            if not piece.vision_direction[index]:
                return False
        return True

    def find_direction_vision(self):
        for index, dirs in enumerate(self.directions):
            self.directions[index] = self.solve_direction(index)
            self.vision[index] = self.solve_vision(index)

        self.vision_handler.modify_map(self.location, self.vision)

    def add(self, other):
        if other not in self.pieces:
            other.tile = self
            self.pieces.append(other)
            self.mix_directions(other.direction)
            self.mix_vision(other.vision_direction)
            for action in other.actions:
                if action not in self.available_actions:
                    self.available_actions[action] = [other]
                else:
                    self.available_actions[action].append(other)

            self.map.changed = True

    def remove(self, other):
        if other in self.pieces:
            other.tile = None
            self.pieces.remove(other)
            self.find_direction_vision()

            for action in other.actions:
                self.available_actions[action].remove(other)
                if not len(self.available_actions[action]):
                    self.available_actions.pop(action)

            self.map.changed = True

    def __le__(self, other):
        return id(self) <= id(other)

    def __lt__(self, other):
        return id(self) < id(other)
