from math import *
import heapq

import numpy as np
import arcade

import constants as c
import isometric

GRID_ISO_DATA = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 320, 0, 160, 320)
SOUTH = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 0, 320, 160, 320)
EAST = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 160, 320, 160, 320)
NORTH = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 320, 320, 160, 320)
WEST = isometric.IsoTexture("assets/iso_select_tile_sheet.png", .0, 20.0, 480, 320, 160, 320)
DIRECTIONS = {0: NORTH, 1: EAST, 2: SOUTH, 3: WEST, 4: GRID_ISO_DATA}


class GridSprite(isometric.IsoSprite):

    def __init__(self, location: tuple, direction=4):
        x, y, z = isometric.cast_to_iso(location[0], location[1], z_mod=0.5)
        super().__init__(location[0], location[1], x, y, z, DIRECTIONS[direction], 0.5)


class GridNode:

    def __init__(self, location: tuple, cost=1):
        self.directions: list[GridNode, GridNode, GridNode, GridNode] = [None, None, None, None]
        self.cost = cost
        self.location: tuple[int, int] = location
        self.node_sprite = GridSprite(location)

    def show_self(self):
        c.iso_append(self.node_sprite)

    def remove_self(self):
        self.node_sprite.remove_from_sprite_lists()

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
        self.points = np.empty([map_data.map_width, map_data.map_height], GridNode)
        self.find_neighbors()

    def find_neighbors(self):
        dirs = ((0, -1), (-1, 0))
        for y_dex, row in enumerate(self.points):
            for x_dex, value in enumerate(row):
                if self.map_data.ground_layer[y_dex][x_dex]:
                    cur_node = GridNode((x_dex, y_dex))
                    self.points[y_dex, x_dex] = cur_node
                    current_tile = self.map_data.layers['wall_layer'].tile_map[x_dex, y_dex]
                    for direction in dirs:
                        n_x = c.clamp(x_dex+direction[0], 0, len(self.points)-1)
                        n_y = c.clamp(y_dex+direction[1], 0, len(row)-1)
                        neighbor_tile = self.map_data.layers["wall_layer"].tile_map[n_x, n_y]
                        neighbor = self.points[n_y, n_x]
                        if n_x != x_dex or n_y != y_dex:
                            cur_neigh_dir = c.DIRECTIONS[direction]
                            neigh_cur_dir = (cur_neigh_dir+2) % 4
                            neigh_check = False
                            cur_check = False

                            if current_tile is None\
                                    or current_tile is not None and current_tile.direction[neigh_cur_dir]:
                                cur_check = True

                            if neighbor_tile is None or\
                                    neighbor_tile is not None and neighbor_tile.direction[cur_neigh_dir]:
                                neigh_check = True

                            if neigh_check and cur_check:
                                if neighbor is not None:
                                    neighbor.directions[neigh_cur_dir] = cur_node

                                if cur_node is not None:
                                    cur_node.directions[cur_neigh_dir] = neighbor
                                # cur_node.directions[cur_neigh_dir] = neighbor
                                # neighbor.directions[neigh_cur_dir] = cur_node

    def draw(self):
        dirs = ((0, -0.25), (0.25, 0), (0, 0.25), (-0.25, 0))
        for y_dex, point_row in enumerate(self.points):
            for x_dex, value in enumerate(point_row):
                if value is not None:
                    for dir_dex, direction in enumerate(dirs):
                        t_x = x_dex+direction[0]
                        t_y = y_dex+direction[1]
                        iso_x, iso_y, iso_z = isometric.cast_to_iso(t_x, t_y)
                        if value.directions[dir_dex] is None:
                            arcade.draw_point(iso_x, iso_y-60, arcade.color.RADICAL_RED, 5)
                        else:
                            arcade.draw_point(iso_x, iso_y-60, arcade.color.WHITE, 5)


def astar_heuristic(a: tuple = (int, int), b: tuple = (int, int)):
    x1, y1 = a
    x2, y2 = b
    return sqrt((x1-x2)**2 + (y1-y2)**2)


def path_2d(grid_2d: PathFindingGrid, start_yx):
    start: GridNode = grid_2d.points[start_yx]
    frontier = PriorityQueue()
    frontier.put(0, start)
    came_from = dict()
    cost_so_far = dict()
    costs_loaded = dict()
    edges = dict()
    came_from[start] = None
    cost_so_far[start] = 0
    costs_loaded[0] = [start]
    if None is start.directions:
        edges[0] = [start]

    while not frontier.empty():
        current = frontier.get()

        for dirs in current.directions:
            if dirs is not None:
                new_cost = cost_so_far[current] + dirs.cost
                if dirs not in cost_so_far or cost_so_far[dirs] > new_cost:
                    cost_so_far[dirs] = new_cost
                    frontier.put(new_cost, dirs)
                    came_from[dirs] = current
                    if new_cost not in costs_loaded:
                        costs_loaded[new_cost] = [dirs]
                    else:
                        costs_loaded[new_cost].append(dirs)
            else:
                current_cost = cost_so_far[current]
                if current_cost not in edges:
                    costs_loaded[current_cost] = [current]
                elif current not in costs_loaded[current_cost].append(current):
                    costs_loaded[current_cost].append(current)

    return came_from, cost_so_far, costs_loaded


def find_edge(max_distance, cost_so_far, costs_loaded):
    edged = []
    for node in costs_loaded[max_distance]:
        for index, direction in enumerate(node.directions):
            sprite = None
            if direction is not None:
                if max_distance < cost_so_far[direction]:
                    sprite = GridSprite(node.location, index)
            else:
                sprite = GridSprite(node.location, index)

            if sprite is not None:
                edged.append(sprite)
                c.iso_append(sprite)
    return edged


def reconstruct_path(grid_2d: PathFindingGrid, came_from: dict, start_yx: tuple, end_yx: tuple):
    start = grid_2d.points[start_yx]
    end = grid_2d.points[end_yx]
    if end is not None:
        current = end
        path: list[GridNode] = []
        while current != start:
            path.append(current)
            current = came_from[current]

        path.reverse()
        return path
    return None
