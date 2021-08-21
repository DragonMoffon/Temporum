import heapq
import math
import random

from typing import List, Tuple

import constants as c
from map_tile import Tile


def find_cost(tile, algorithm):
    if algorithm == "base":
        return 1
    elif algorithm == "target_player":
        return int(math.sqrt(astar_heuristic(tile.location, (c.PLAYER.e_x, c.PLAYER.e_y))))


class PriorityQueue:
    def __init__(self):
        self.elements: List[Tuple[float, Tile]] = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, priority, tile):
        heapq.heappush(self.elements, (priority, tile))

    def get(self):
        return heapq.heappop(self.elements)[1]


def find_neighbours(tile_map):
    dirs = (0, -1), (-1, 0)
    for x_dex, column in enumerate(tile_map):
        for y_dex, current_tile in enumerate(column):
            if current_tile is not None:
                current_tile.location = (x_dex, y_dex)
                for direction in dirs:
                    n_x = x_dex + direction[0]
                    n_y = y_dex + direction[1]
                    if 0 <= n_y < len(column) and 0 <= n_x < len(tile_map):
                        neighbor_tile = tile_map[n_x, n_y]
                        cur_neigh_dir = c.DIRECTIONS[direction]
                        neigh_cur_dir = (cur_neigh_dir + 2) % 4

                        if current_tile is not None and neighbor_tile is not None:
                            neighbor_tile.neighbours[neigh_cur_dir] = current_tile
                            current_tile.neighbours[cur_neigh_dir] = neighbor_tile


def astar_heuristic(a: tuple = (int, int), b: tuple = (int, int)):
    x1, y1 = a
    x2, y2 = b
    return (x1-x2)**2 + (y1-y2)**2


def path_2d(grid_2d, start_xy, max_dist: int = 20, algorithm="base"):
    """
    :param grid_2d: The Grid That has the GridNodes and other data
    :param start_xy: The starting x and y position.
    :param max_dist: The maximum distance a tile can be before it stops processing.
    :param algorithm: which algorithm to use when calculating the
    :return: The came_from and cost_so_far dictionaries, costs_loaded and edges.
    """
    start = grid_2d[start_xy]

    frontier = PriorityQueue()
    frontier.put(0, start)
    # came_from uses a GridNode as a key and gives another grid node which it came from. This Dict is used to create
    # paths that go from the end to the start.
    came_from = dict()
    # cost_so_far uses a Tile as a key and gives how much this node costs in initiative.
    cost_so_far = dict()
    # costs_loaded uses a float as a key and gives a list of all the nodes that have this cost. So all nodes with a cost
    # of 1 are stored in a list, all nodes with a cost of 2 are in a list etc.
    costs_loaded = dict()
    # priority_loaded uses a float as a key and gives a list of all the nodes that had this priority. This is so a path
    # can be found even if the target is unreachable.
    priority_loaded = dict()
    # edges is a list of all nodes that have and edge.
    edges = []

    # Sets up the start node in all of the lists.
    came_from[start] = None
    cost_so_far[start] = 0
    priority_loaded[start] = find_cost(start, algorithm)
    costs_loaded[0] = [start]
    if None in start.directions:
        edges.append(start)

    # The Path Grid Loop.
    while not frontier.empty():
        # Gets the GridNode with the lowest cost.
        current = frontier.get()

        # Looks at each direction in the GridNode for the next in the path.
        for index, dirs in enumerate(current.neighbours):
            # If there is a connection in this direction
            # check if these two nodes can connect.
            dir_to_current = (index + 2) % 4
            # find the cost for this node.
            new_cost = cost_so_far[current] + 1
            # If the dir is new or the cost is lower than the previous cost add it to the queue
            if (dirs is not None
                    and dirs.directions[dir_to_current] and current.directions[index]
                    and 'move' in dirs.available_actions and new_cost <= max_dist
                    and (dirs not in cost_so_far or new_cost < cost_so_far[dirs])):

                priority = find_cost(dirs, algorithm)
                cost_so_far[dirs] = new_cost
                frontier.put(priority, dirs)
                came_from[dirs] = current
                if new_cost not in costs_loaded:
                    costs_loaded[new_cost] = [dirs]
                else:
                    costs_loaded[new_cost].append(dirs)

                if priority not in priority_loaded:
                    priority_loaded[priority] = [dirs]
                elif dirs not in priority_loaded[priority]:
                    priority_loaded[priority].append(dirs)
            else:
                # If the current tile has a neighbour that is past the max dist it is an edge
                # If there is a neighbor node but they do not connect it is an edge
                # If the node has a none in a direction then it is an edge.
                if current not in edges:
                    edges.append(current)

    edges = sorted(edges, key=lambda edge: cost_so_far[edge])
    return came_from, cost_so_far, costs_loaded, edges


def path_to_target(grid_2d, start_xy, target_xy, max_dist):
    start = grid_2d[start_xy]
    end = grid_2d[target_xy]
    dirs = (0, 1), (0, -1), (1, 0), (-1, 0)
    best = float('inf')
    best_pos = target_xy
    while end is None:
        for direction in dirs:
            pos = c.clamp(best_pos[0] + direction[0], 0, len(grid_2d) - 1), \
                  c.clamp(best_pos[1] + direction[1], 0, len(grid_2d[0]) - 1)
            distance = astar_heuristic(pos, start_xy)
            if distance < best:
                best_pos = pos
                best = distance
                end = grid_2d[pos]

    frontier = PriorityQueue()
    frontier.put(0, start)

    came_from = dict()
    cost_so_far = dict()
    priority_loaded = dict()

    came_from[start] = None
    cost_so_far[start] = 0

    found = False

    while not frontier.empty():
        current = frontier.get()
        if current == end:
            found = True
            break
        for index, dirs in enumerate(current.neighbours):
            if dirs is not None:
                dir_to_current = (index + 2) % 4
                if dirs.directions[dir_to_current] and current.directions[index] and 'move' in dirs.available_actions:
                    new_cost = cost_so_far[current] + 1
                    if new_cost <= max_dist + 10:
                        if dirs not in cost_so_far or new_cost < cost_so_far[dirs]:
                            cost_so_far[dirs] = new_cost
                            came_from[dirs] = current

                            priority = astar_heuristic(dirs.location, end.location) + new_cost
                            frontier.put(priority, dirs)

                            if priority not in priority_loaded:
                                priority_loaded[priority] = [dirs]
                            elif dirs not in priority_loaded[priority]:
                                priority_loaded[priority].append(dirs)

    if not found:
        end = random.choice(list(cost_so_far.keys()))

    if end is not None and end in came_from:
        current = end
        path: list = []
        while current != start:
            path.append(current)
            if current in came_from:
                current = came_from[current]
            else:
                return []
        path.reverse()
        return path
    return []


def reconstruct_path(grid_2d, came_from: dict, start_xy: tuple, end_xy: tuple):
    start = grid_2d[start_xy]
    end = grid_2d[end_xy]
    dirs = (0, 1), (0, -1), (1, 0), (-1, 0)
    while end is None:
        best = int('inf')
        for direction in dirs:
            pos = c.clamp(end_xy[0]+direction[0], 0, len(grid_2d)-1),\
                  c.clamp(end_xy[1]+direction[1], 0, len(grid_2d[0])-1)
            distance = astar_heuristic(pos, start_xy)
            if distance < best:
                new_end = grid_2d[pos]
                best = distance
                end = new_end

    if end is not None and end in came_from:
        current = end
        path: list = []
        while current != start:
            path.append(current)
            if current in came_from:
                current = came_from[current]
            else:
                return []
        path.reverse()
        return path
    return []


def create_bot(x, y, grid_2d):
    import isometric
    import turn

    bot_text = isometric.generate_iso_data_other('bot')

    class SimpleMoveBot(isometric.IsoActor):

        def __init__(self):
            super().__init__(x, y, bot_text[0], 6)
            self.textures = bot_text
            self.set_grid(grid_2d)
            self.algorithm = 'target_player'
            self.last_known_player_location = None
            self.shock_timer = 0

        def new_pos(self, e_x, e_y):
            super().new_pos(e_x, e_y)
            if not c.PLAYER.game_view.map_handler.map.check_seen((e_x, e_y)):
                c.iso_remove(self)
            else:
                c.iso_append(self)

        def update(self):
            if self.action_handler.current_action is None and self.action_handler.initiative > 0:
                if self.shock_timer:
                    self.set_iso_texture(self.textures[1])
                    self.shock_timer -= 1
                    self.action_handler.pass_turn()
                else:
                    self.set_iso_texture(self.textures[0])
                    move_node = c.PLAYER.game_view.map_handler.full_map[c.PLAYER.e_x, c.PLAYER.e_y]
                    self.action_handler.current_action = turn.ACTIONS['move_enemy'](move_node.available_actions['move'],
                                                                                    self.action_handler)

        def hit(self, shooter):
            self.shock_timer = 4
            self.set_iso_texture(self.textures[1])

    return SimpleMoveBot()
