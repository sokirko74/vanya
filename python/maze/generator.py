import random
from enum import Enum
import numpy as np


class Direction(Enum):
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)


WALKABLE_TILE = 1
WALL_TILE = 2
START_TILE = 3
TARGET_TILE = 4


def add_tuples(a, b):
    return a[0] + b[0], a[1] + b[1]


class Generator:
    def __init__(self, grid_rows=40, grid_cols=75, min_rooms=3, max_rooms=4, min_room_connections=2, max_room_size=100,
                 allow_redundant_connections=False, distance_to_target=75, path_width=4):
        self.rows = grid_rows
        self.cols = grid_cols
        self.min_rooms = min_rooms
        self.max_rooms = max_rooms
        self.min_room_connections = min_room_connections
        self.max_room_size = max_room_size
        self.allow_redundant_connections = allow_redundant_connections
        self.distance_to_target = distance_to_target
        self.path_width = path_width
        self.start = (0, 0)
        self.target_room_source = (0, 0)
        self.targets = []
        self.padding = 0
        self.grid = None
        self.init_grid()
        self.maze_rooms_sources = []
        self.maze_rooms = []
        self.maze_rooms_groups = []

    def init_grid(self):
        self.grid = np.zeros((self.rows, self.cols), dtype=int)

    def clear(self):
        self.maze_rooms.clear()
        self.maze_rooms_sources.clear()
        self.init_grid()

    def _generate_maze_rooms_groups(self):
        room_amount = random.randint(self.min_rooms, self.max_rooms)
        positions = set()
        for i in range(room_amount):
            x = random.randint(0, self.cols - 1)
            y = random.randint(0, self.rows - 1)
            if (x, y) in positions:
                i -= 1
                continue
            positions.add((x, y))
        # choose some random points on the grid as room sources
        for pos in positions:
            self.grid[pos[1]][pos[0]] = WALKABLE_TILE
            self.maze_rooms_sources.append((pos[0], pos[1]))
            self.maze_rooms.append([(pos[0], pos[1]), (pos[0], pos[1]), (pos[0], pos[1]), (pos[0], pos[1])])
        self.maze_rooms_groups = [[x] for x in self.maze_rooms_sources]

    def _extend_rooms(self):
        # "grow" the rooms around the sources until they collide
        for _ in range(self.max_room_size):
            for room in self.maze_rooms:
                for i, d in enumerate(Direction):
                    a, b = self.__extend_if_available(room[i], room[(i + 1) % 4], d.value)
                    if a != -1:
                        room[i] = a
                        room[(i + 1) % 4] = b

    def _connect_rooms(self):
        # connect the room sources with a greedy search
        for p in self.maze_rooms_sources:
            distances = []
            for i, c in enumerate(self.maze_rooms_sources):
                if c == p: continue
                distances.append((self.__get_distance(c, p), i))
            distances.sort(key=lambda x: x[0])
            closest_rooms = distances[:self.min_room_connections]
            for room in closest_rooms:
                r = self.maze_rooms_sources[room[1]]
                if not self.allow_redundant_connections:
                    p_ind = [i for i, row in enumerate(self.maze_rooms_groups) for a in row if a == p][0]
                    r_ind = [i for i, row in enumerate(self.maze_rooms_groups) for a in row if a == r][0]
                    if p_ind == r_ind: continue
                self.__path(p, r)

    def _test_rooms_are_reachable(self):
        # verify every room is reachable
        while len(self.maze_rooms_groups) > 1:
            self.maze_rooms_groups.sort(key=lambda x: len(x))
            p1 = self.maze_rooms_groups[0][random.randint(0, len(self.maze_rooms_groups[0])) - 1]
            distances = []
            for i, c in enumerate(self.maze_rooms_groups[1]):
                distances.append((self.__get_distance(c, p1), i))
            distances.sort(key=lambda x: x[0])
            p2 = self.maze_rooms_groups[1][distances[0][1]]
            self.__path(p1, p2)

    def _choose_start_and_end_room(self):
        # choose start and target room
        ind_1 = random.randint(0, len(self.maze_rooms_sources) - 1)
        self.start = self.maze_rooms_sources[ind_1]
        if self.distance_to_target == 0:
            ind_2 = random.randint(0, len(self.maze_rooms_sources) - 1)
            if ind_2 >= ind_1:
                ind_2 += 1
            self.target_room_source = self.maze_rooms_sources[ind_2]
        else:
            distances = []
            for c in self.maze_rooms_sources:
                distances.append((self.__get_distance(c, self.start), c))
            distances.sort(key=lambda x: x[0])
            ind_2 = int(float(len(distances)) * (float(self.distance_to_target) / 100))
            if ind_2 >= len(distances): ind_2 = len(distances) - 1
            self.target_room_source = distances[ind_2][1]
        self.grid[self.start[1]][self.start[0]] = START_TILE

    def _generate_exit(self):
        found = False
        for d in Direction:
            if found: break
            cur_pos = self.target_room_source
            while self.grid[cur_pos[1]][cur_pos[0]] != WALL_TILE:
                cur_pos = add_tuples(cur_pos, d.value)
            pos = add_tuples(cur_pos, d.value)
            if not self.__check_bounds(pos) or self.grid[pos[1]][pos[0]] == 0:
                found = True
                self.grid[cur_pos[1]][cur_pos[0]] = TARGET_TILE
                d1 = (d.value[1], d.value[0])
                d2 = (-d.value[1], -d.value[0])
                i = self.path_width - 1
                dirs = [d1, d2]
                for x in dirs:
                    cur_pos_2 = cur_pos
                    while i > 0:
                        cur_pos_2 = add_tuples(cur_pos_2, x)
                        if self.grid[cur_pos_2[1]][cur_pos_2[0]] != WALL_TILE:
                            break
                        cur_pos_3 = add_tuples(cur_pos_2, d.value)
                        if self.__check_bounds(cur_pos_3):
                            if self.grid[cur_pos_3[1]][cur_pos_3[0]] == WALL_TILE:
                                break
                        cur_pos_4 = add_tuples(cur_pos_2, (-d.value[0], -d.value[1]))
                        if self.__check_bounds(cur_pos_4):
                            if self.grid[cur_pos_4[1]][cur_pos_4[0]] == WALL_TILE:
                                break
                        self.grid[cur_pos_2[1]][cur_pos_2[0]] = TARGET_TILE
                        i -= 1
        if not found:
            self.grid[self.target_room_source[1]][self.target_room_source[0]] = TARGET_TILE

    def __path(self, p1, p2):
        cur_pos = (p1[0], p1[1])
        count = 0
        while cur_pos != p2:
            vals = []
            for d in Direction:
                new_pos = add_tuples(cur_pos, d.value)
                if not self.__check_bounds(new_pos): continue
                vals.append((self.__grid_weight(new_pos) + self.__get_distance(new_pos, p2), new_pos, d.value))
            vals.sort(key=lambda x: x[0])
            if len(vals) == 0:
                return
            cur_pos = vals[0][1]
            path_width_pos = (cur_pos[0], cur_pos[1])
            low = add_tuples(cur_pos, (-vals[0][2][1], -vals[0][2][0]))
            if self.grid[low[1]][low[0]] != WALKABLE_TILE:
                self.grid[low[1]][low[0]] = WALL_TILE
            for i in range(self.path_width):
                self.grid[path_width_pos[1]][path_width_pos[0]] = WALKABLE_TILE
                path_width_pos = add_tuples(path_width_pos, (vals[0][2][1], vals[0][2][0]))
                if self.grid[path_width_pos[1]][path_width_pos[0]] != WALKABLE_TILE:
                    self.grid[path_width_pos[1]][path_width_pos[0]] = WALL_TILE
                wall_1 = add_tuples(path_width_pos, (vals[0][2][0], vals[0][2][1]))
                wall_2 = add_tuples(path_width_pos, (-vals[0][2][0], -vals[0][2][1]))
                if self.grid[wall_1[1]][wall_1[0]] != WALKABLE_TILE:
                    self.grid[wall_1[1]][wall_1[0]] = WALL_TILE
                if self.grid[wall_2[1]][wall_2[0]] != WALKABLE_TILE:
                    self.grid[wall_2[1]][wall_2[0]] = WALL_TILE
            count += 1
            if count > self.rows * self.cols:
                return
        self.__update_groups(p1, p2)

    def __update_groups(self, p1, p2):
        p1_ind = [i for i, row in enumerate(self.maze_rooms_groups) for a in row if a == p1][0]
        p2_ind = [i for i, row in enumerate(self.maze_rooms_groups) for a in row if a == p2][0]
        if p1_ind != p2_ind:
            self.maze_rooms_groups[p1_ind] = self.maze_rooms_groups[p1_ind] + self.maze_rooms_groups[p2_ind]
            self.maze_rooms_groups.remove(self.maze_rooms_groups[p2_ind])

    def __check_bounds(self, pos):
        if pos[0] >= len(self.grid[0]) or pos[0] < 0:
            return False
        if pos[1] >= len(self.grid) or pos[1] < 0:
            return False
        if self.grid[pos[1]][pos[0]] == -1:
            return False
        return True

    def __grid_weight(self, pos):
        p = self.grid[pos[1]][pos[0]]
        if p == 0:
            return 1.5
        elif p == WALKABLE_TILE:
            return 0.
        elif p == WALL_TILE:
            return 1.75
        else:
            return 9999

    def __get_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def __extend_if_available(self, v1, v2, dir):
        start = add_tuples(v1, dir)
        end = add_tuples(v2, dir)
        if not self.__check_bounds(start):
            return -1, 0

        extend_dir = (0, 0)
        if dir == Direction.UP.value:
            extend_dir = Direction.RIGHT.value
        elif dir == Direction.RIGHT.value:
            extend_dir = Direction.DOWN.value
        elif dir == Direction.DOWN.value:
            extend_dir = Direction.LEFT.value
        elif dir == Direction.LEFT.value:
            extend_dir = Direction.UP.value

        cur_pos = start
        while cur_pos != end:
            val = self.grid[cur_pos[1]][cur_pos[0]]
            if val == WALL_TILE or not self.__check_bounds(cur_pos): return -1, 0
            cur_pos = add_tuples(cur_pos, extend_dir)
        if self.grid[end[1]][end[0]] == WALKABLE_TILE or self.grid[end[1]][end[0]] == WALL_TILE:
            return -1, 0

        cur_pos = start
        cur_pos2 = v1
        draw_white = False
        while cur_pos != end:
            self.grid[cur_pos[1]][cur_pos[0]] = WALL_TILE
            if draw_white: self.grid[cur_pos2[1]][cur_pos2[0]] = WALKABLE_TILE
            draw_white = True
            cur_pos = add_tuples(cur_pos, extend_dir)
            cur_pos2 = add_tuples(cur_pos2, extend_dir)
        self.grid[end[1]][end[0]] = WALL_TILE
        self.grid[start[1]][start[0]] = WALL_TILE

        return start, end

    def generate_maze(self):
        for i in range(20):
            try:
                self.init_grid()
                self._generate_maze_rooms_groups()
                self._extend_rooms()
                self._connect_rooms()
                self._test_rooms_are_reachable()
                self._choose_start_and_end_room()
                self._generate_exit()
                return
            except IndexError as exp:
                print (exp)
                random.seed()
        raise Exception("cannot generate maze")

