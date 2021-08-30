import heapq
import math

from typing import List, Tuple

import constants as c
from map_tile import Tile


def find_cost(tile, algorithm) -> int:
    """
    using the input algorithm find the cost of a tile. This is so the Ai can sneak around the player. It avoids being
    seen by the player, and avoids it when possible. While still staying as close to the player as possible.
    :param tile: The Current Tile To find cost.
    :param algorithm: What style to find the cost for.
    :return: the cost.
    """
    if algorithm == "base":
        return 1
    elif algorithm == "target_player":
        if tile in c.PLAYER.path_finding_data[1]:
            closeness = c.PLAYER.path_finding_data[1][tile]
        else:
            closeness = int(math.sqrt(astar_heuristic(tile.location, (c.PLAYER.e_x, c.PLAYER.e_y))))
        seen = tile.map.vision_handler.vision_image.getpixel(tile.location)[0]
        return closeness + seen


class PriorityQueue:
    """
    This uses the fast sorting path of a Priority Que to find the the best tile to pick based on priority.
    """
    def __init__(self):
        self.elements: List[Tuple[float, Tile]] = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, priority, tile):
        heapq.heappush(self.elements, (priority, tile))

    def get(self):
        return heapq.heappop(self.elements)[1]


def find_neighbours(tile_map):
    """
    This is run to link all the tiles together. But only where there actually are tiles.

    :param tile_map: The 2d array of tiles to go through.
    """
    # It only looks backwards so that it doesn't ever do the same operation twice while still finding the neighbors for
    # every tile.
    dirs = (0, -1), (-1, 0)

    # Iterate through tile map.
    for x_dex, column in enumerate(tile_map):
        for y_dex, current_tile in enumerate(column):

            # If the tile isn't none check each direction.
            if current_tile is not None:
                current_tile.location = (x_dex, y_dex)
                for direction in dirs:

                    # Find the x and y pos of the neighbor tile.
                    n_x = x_dex + direction[0]
                    n_y = y_dex + direction[1]

                    # If the check pos is inside the map.
                    if 0 <= n_y < len(column) and 0 <= n_x < len(tile_map):
                        # find the neighbor and the direction index to the tile and from the tile.
                        neighbor_tile = tile_map[n_x, n_y]
                        cur_neigh_dir = c.DIRECTIONS[direction]
                        neigh_cur_dir = (cur_neigh_dir + 2) % 4

                        # if both tiles aren't none set the tiles to be neighbors.
                        if current_tile is not None and neighbor_tile is not None:
                            neighbor_tile.neighbours[neigh_cur_dir] = current_tile
                            current_tile.neighbours[cur_neigh_dir] = neighbor_tile


def astar_heuristic(a: tuple = (int, int), b: tuple = (int, int)):
    # Find the non sqrt distance between two tiles. C^2 = A^2 + B^2
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

    # frontier uses the maths behind Queues to quickly sort the next possible tiles to search by whichever has the
    # lowest priority.
    frontier = PriorityQueue()
    frontier.put(0, start)

    # tile_costs this uses the same Queue math but this time to sorts by just the cost of the tiles.
    # this is so the ai algorithms can find the best tile to go to.
    tile_costs = PriorityQueue()
    tile_costs.put(find_cost(start, algorithm), start)

    # came_from uses a GridNode as a key and gives another grid node which it came from. This Dict is used to create
    # paths that go from the end to the start.
    came_from = dict()
    # cost_so_far uses a Tile as a key and gives how much this node costs in initiative.
    cost_so_far = dict()
    # priority_so_far is the same as cost_so_far but uses the priority stacked on top of itself.
    priority_so_far = dict()
    # edges is a list of all nodes that have and edge.
    edges = []

    # Sets up the start node in all of the lists.
    came_from[start] = None
    cost_so_far[start] = 0
    priority_so_far[start] = 0
    if None in start.directions:
        edges.append(start)

    # The Path Grid Loop.
    while not frontier.empty():
        # Gets the GridNode with the lowest cost.
        current = frontier.get()

        # Looks at each direction in the GridNode for the next in the path.
        for index, dirs in enumerate(current.neighbours):
            if dirs is not None:
                # If there is a neighbor in this direction
                # check if these two nodes can connect.
                dir_to_current = (index + 2) % 4

                # find the cost for this node.
                new_cost = cost_so_far[current] + 1
                priority = find_cost(dirs, algorithm)
                new_priority = priority_so_far[current] + priority
                # If the dir is new or the cost is lower than the previous cost add it to the queue
                if (dirs.directions[dir_to_current] and current.directions[index]
                        and 'move' in dirs.available_actions and new_cost <= max_dist
                        and (dirs not in priority_so_far or new_priority < priority_so_far[dirs])
                        and dirs is not came_from[current]):

                    # This adds the tiles priority (no matter how they got to the tile. Just how much this tile costs)
                    tile_costs.put(priority, dirs)

                    # take the new cost and set the new tiles cost so far. This is so the player can find the edges.
                    cost_so_far[dirs] = new_cost

                    # Add the dir to came from with the last tile as how it travelled. For reconstructing paths.
                    came_from[dirs] = current

                    # add the priority to the que.
                    priority_so_far[dirs] = new_priority
                    frontier.put(new_priority, dirs)

                    continue

            # If the current tile has a neighbour that is past the max dist it is an edge
            # If there is a neighbor node but they do not connect it is an edge
            # If the node has a none in a direction then it is an edge.
            if current not in edges:
                edges.append(current)

    edges = sorted(edges, key=lambda edge: cost_so_far[edge])
    return came_from, cost_so_far, edges, tile_costs


def reconstruct_path(grid_2d, came_from: dict, start_xy: tuple, end_xy: tuple):
    """
    Taking the start and end pos it reconstructs the path. This is split from generating the Path_2d because multiple
    paths may be calculated from the same path_2d map.

    :param grid_2d: The 2d grid of tiles to retrieve from.
    :param came_from: the dict of every reachable tile and what tile that tile came from.
    :param start_xy: the start x and y pos
    :param end_xy: the end x and y pos.
    :return:
    """

    # find the start and end tiles.
    start = grid_2d[start_xy]
    end = grid_2d[end_xy]

    # If the tile is accessible then the set the current to end. Then loop through the came from dict until the start is
    # found.
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
