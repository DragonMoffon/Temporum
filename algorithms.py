import heapq
import random

import constants as c


def find_cost(tile):
    return 1


class PriorityQueue:
    def __init__(self):
        self.elements: list[tuple[float, object]] = []

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


def path_2d(grid_2d, start_yx, max_dist: int = 20):
    """
    :param grid_2d: The Grid That has the GridNodes and other data
    :param start_yx: The starting x and y position.
    :param max_dist: The maximum distance a tile can be before it stops processing.
    :return: The came_from and cost_so_far dictionaries, and if player is true it also returns costs_loaded and edges.
    """
    start = grid_2d[start_yx]
    frontier = PriorityQueue()
    frontier.put(0, start)
    # came_from uses a GridNode as a key and gives another grid node which it came from. This Dict is used to create
    # paths that go from the end to the start.
    came_from = dict()
    # cost_so_far uses a Tile as a key and gives how much this node costs.
    cost_so_far = dict()
    # costs_loaded uses a float as a key and gives a list of all the nodes that have this cost. So all nodes with a cost
    # of 1 are stored in a list, all nodes with a cost of 2 are in a list etc.
    costs_loaded = dict()
    # edges is a list of all nodes that have and edge.
    edges = []

    # Sets up the start node in all of the lists.
    came_from[start] = None
    cost_so_far[start] = 0
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
            if dirs is not None:
                # check if these two nodes can connect.
                dir_to_current = (index + 2) % 4
                if dirs.directions[dir_to_current] and current.directions[index] and 'move' in dirs.available_actions:
                    # find the cost for this node.
                    new_cost = cost_so_far[current] + find_cost(dirs)
                    if new_cost <= max_dist:
                        # If the cost is new or lower than the previous cost add it to the queue
                        if dirs not in cost_so_far or cost_so_far[dirs] > new_cost:
                            cost_so_far[dirs] = new_cost
                            frontier.put(new_cost, dirs)
                            came_from[dirs] = current
                            if new_cost not in costs_loaded:
                                costs_loaded[new_cost] = [dirs]
                            else:
                                costs_loaded[new_cost].append(dirs)
                else:
                    # If there is a neighbor node but they do not connect it is an edge
                    pass
                    if current not in edges:
                        edges.append(current)
            else:
                # If the node has a none in a direction then it is an edge.
                if current not in edges:
                    edges.append(current)

    edges = sorted(edges, key=lambda edge: cost_so_far[edge])
    return came_from, cost_so_far, costs_loaded, edges


def reconstruct_path(grid_2d, came_from: dict, start_xy: tuple, end_xy: tuple):
    start = grid_2d[start_xy]
    end = grid_2d[end_xy]
    if end is None:
        best = int('inf')
        dirs = (0, 1), (0, -1), (1, 0), (-1, 0)
        for direction in dirs:
            pos = c.clamp(end_xy[1]+direction[0], 0, 19), c.clamp(end_xy[0]+direction[1], 0, 19)
            distance = astar_heuristic(pos, start_xy)
            if distance < best:
                new_end = grid_2d[pos]
                if new_end is not None:
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


def create_bot(e_x, e_y, grid_2d):
    import isometric
    import turn

    bot_text = isometric.generate_iso_data_other('bot')[0]

    class SimpleMoveBot(isometric.IsoActor):

        def __init__(self):
            super().__init__(e_x, e_y, bot_text)
            self.set_grid(grid_2d)

        def update(self):
            if self.action_handler.current_action is None and self.action_handler.initiative > 0:
                self.load_paths()
                move_node = random.choice(self.path_finding_data[2].get(self.action_handler.initiative,
                                                                        self.path_finding_data[2].get(
                                                                            self.action_handler.initiative//2,
                                                                            self.path_finding_data[2][0])))
                move_location = move_node.available_actions['move'][0]
                self.action_handler.current_action = turn.ACTIONS['move']([move_location],
                                                                          self.action_handler)

    return SimpleMoveBot()
