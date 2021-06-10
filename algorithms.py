import heapq
import numpy as np

import constants as c


class GridNode:

    def __init__(self, location: tuple, cost=1):
        self.directions: list[GridNode, GridNode, GridNode, GridNode] = [None, None, None, None]
        self.cost = cost
        self.location: tuple[int, int] = location

    def __le__(self, other):
        return id(self) <= id(other)

    def __lt__(self, other):
        return id(self) < id(other)


class PriorityQueue:
    def __init__(self):
        self.elements: list[tuple[float, GridNode]] = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, priority, grid_node):
        heapq.heappush(self.elements, (priority, grid_node))

    def get(self) -> GridNode:
        return heapq.heappop(self.elements)[1]


class PathFindingGrid:

    def __init__(self, map_data):
        self.map_data = map_data
        self.points = np.empty([c.CURRENT_MAP_SIZE[1], c.CURRENT_MAP_SIZE[0]], GridNode)
        self.find_neighbors()

    def find_neighbors(self):
        dirs = ((0, -1), (-1, 0))
        for y_dex, row in enumerate(self.points):
            for x_dex, value in enumerate(row):
                if self.map_data.ground_layer[y_dex][x_dex]:
                    cur_node = GridNode((x_dex, y_dex))
                    self.points[y_dex, x_dex] = cur_node
                    current_tile = self.map_data.layers['1']['wall'].tile_map[x_dex, y_dex]
                    for direction in dirs:
                        n_x = x_dex+direction[0]
                        n_y = y_dex+direction[1]
                        if n_x < len(row) and n_y < len(self.points):
                            neighbor_tile = self.map_data.layers['1']['wall'].tile_map[n_x, n_y]
                            neighbor = self.points[n_y, n_x]
                            cur_neigh_dir = c.DIRECTIONS[direction]
                            neigh_cur_dir = (cur_neigh_dir+2) % 4
                            neigh_check = False
                            cur_check = False

                            if current_tile is None\
                                    or current_tile[0] is not None and current_tile[0].direction[neigh_cur_dir]:
                                cur_check = True

                            if neighbor_tile is None or\
                                    neighbor_tile[0] is not None and neighbor_tile[0].direction[cur_neigh_dir]:
                                neigh_check = True

                            if neigh_check and cur_check:
                                if neighbor is not None:
                                    neighbor.directions[neigh_cur_dir] = cur_node

                                if cur_node is not None:
                                    cur_node.directions[cur_neigh_dir] = neighbor
                                # cur_node.directions[cur_neigh_dir] = neighbor
                                # neighbor.directions[neigh_cur_dir] = cur_node


def astar_heuristic(a: tuple = (int, int), b: tuple = (int, int)):
    x1, y1 = a
    x2, y2 = b
    return (x1-x2)**2 + (y1-y2)**2


def path_2d(grid_2d: PathFindingGrid, start_yx, max_dist: int = 20):
    """
    :param grid_2d: The Grid That has the GridNodes and other data
    :param start_yx: The starting x and y position.
    :param max_dist: The maximum distance a tile can be before it stops processing.
    :return: The came_from and cost_so_far dictionaries, and if player is true it also returns costs_loaded and edges.
    """
    start: GridNode = grid_2d.points[start_yx]
    frontier = PriorityQueue()
    frontier.put(0, start)
    # came_from uses a GridNode as a key and gives another grid node which it came from. This Dict is used to create
    # paths that go from the end to the start.
    came_from = dict()
    # cost_so_far uses a Gridnode as a key and gives how much this node costs.
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
        for dirs in current.directions:
            # If there is a connection in this direction
            if dirs is not None:
                # find the cost for this node.
                new_cost = cost_so_far[current] + dirs.cost
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
                # If the node has a none in a direction then it is an edge.
                if current not in edges:
                    edges.append(current)

    edges = sorted(edges, key=lambda edge: cost_so_far[edge])
    return came_from, cost_so_far, costs_loaded, edges


def reconstruct_path(grid_2d: PathFindingGrid, came_from: dict, start_yx: tuple, end_yx: tuple):
    start = grid_2d.points[start_yx]
    end = grid_2d.points[end_yx]
    if end is None:
        best = 10000
        dirs = (0, 1), (0, -1), (1, 0), (-1, 0)
        for direction in dirs:
            pos = c.clamp(end_yx[1]+direction[0], 0, 19), c.clamp(end_yx[0]+direction[1], 0, 19)
            distance = astar_heuristic(pos, (start_yx[1], start_yx[0]))
            if distance < best:
                new_end = grid_2d.points[(pos[1], pos[0])]
                if new_end is not None:
                    best = distance
                    end = new_end

    if end is not None or end not in came_from:
        current = end
        path: list[GridNode] = []
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

    bot_text = isometric.generate_iso_data_other('bot')[0]

    class SimpleMoveBot(isometric.IsoActor):

        def __init__(self):
            super().__init__(e_x, e_y, bot_text)
            self.set_grid(grid_2d)

    return SimpleMoveBot()
