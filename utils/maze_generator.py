import random
import numpy as np
import pygame
from collections import defaultdict
from pygame.math import Vector2

WALKABLE_TILE = 1
WALL_TILE = 2
TARGET_TILE = 4


def get_room_rect_with_walls(room_without_walls):
    r = room_without_walls.copy()
    r.left -= 1
    r.top -= 1
    r.width += 2
    r.height += 2
    return r


def get_rect_intersection(rect1, rect2):
    left = max(rect1.left, rect2.left)
    top = max(rect1.top, rect2.top)
    width = min(rect1.right, rect2.right) - left
    height = min(rect1.bottom, rect2.bottom) - top
    return pygame.Rect(left, top, width, height)

class TRoomPlace:
    def __init__(self, parent, room_index, coord: Vector2, type="corner_place"):
        self.parent = parent
        self.room_index = room_index
        self.coord = coord
        self.type = type # can be center or corner

    def is_in_closed_room(self):
        return self.parent.room_to_doors[self.room_index] == 0
    def is_in_start_room(self):
        return self.parent.start_room_index == self.room_index



class Generator:
    def __init__(self,  logger, rooms=2, door_width=8):
        self.logger = logger
        self.grid_width = None
        self.grid_height = None
        self.inner_rooms_count = rooms
        self.door_width = door_width
        self.grid = None
        self.maze_rooms = []
        self.main_room = None
        self.start_pos = None
        self.room_places = None
        self.adjacent_rooms = None
        self.start_room_index = None
        self.exit_room_index = None
        self.room_to_doors = defaultdict(int)

    def get_new_place(self, type, can_be_start_room=True, can_be_closed=True):
        random.shuffle(self.room_places)
        i: TRoomPlace
        for i in self.room_places:
            if i.is_in_start_room() and not can_be_start_room:
                continue
            if type != i.type:
                continue
            if not can_be_closed  and i.is_in_closed_room():
                continue
            self.room_places.remove(i)
            return i.coord

    def _find_room_by_point(self, x, y):
        for index, room in enumerate(self.maze_rooms):
            if room.collidepoint((x, y)):
                return index
        # this point is in a wall
        return None

    def wall_can_contain_a_door(self, wall_len):
        return wall_len >= self.door_width + 2

    def _find_random_room(self):
        for _ in range(10):
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            room_index = self._find_room_by_point(x, y)
            if room_index is None:
                continue
            room = self.maze_rooms[room_index]
            if self.wall_can_contain_a_door(max(room.width, room.height) / 2):
                return room_index

        for room_index, room in enumerate(self.maze_rooms):
            if self.wall_can_contain_a_door(max(room.width, room.height) / 2):
                return room_index

        max_room = max(self.maze_rooms, key=lambda x: max(x.width,x.height))
        return self.maze_rooms.index(max_room)

    def _divide_room(self, room: pygame.Rect):
        not_equal_padding = 1
        if room.width > room.height:
            # a vertical wall
            wall_pos = random.randint(int(room.width / 2 - not_equal_padding), int(room.width / 2 + not_equal_padding))
            room1 = pygame.Rect(room.left,      room.top, wall_pos, room.height)
            room2 = pygame.Rect(room1.right + 1, room.top, room.width - room1.width - 1, room.height)
        else:
            # a horizontal wall
            wall_pos = random.randint(int(room.height / 2 - not_equal_padding), int(room.height / 2 + not_equal_padding))
            room1 = pygame.Rect(room.left, room.top,         room.width, wall_pos)
            room2 = pygame.Rect(room.left, room1.bottom + 1, room.width, room.height - room1.height - 1)

        assert self.main_room.contains(room1)
        assert self.main_room.contains(room2)
        return [room1, room2]

    def _generate_rooms(self):

        self.main_room = pygame.Rect(1, 1, self.grid_width - 2, self.grid_height - 2)
        self.maze_rooms.clear()
        self.maze_rooms.extend(self._divide_room(self.main_room))

        for i in range(self.inner_rooms_count - 2):
            room_index = self._find_random_room()
            new_rooms = self._divide_room(self.maze_rooms.pop(room_index))
            self.maze_rooms.extend(new_rooms)
        assert len(self.maze_rooms) == self.inner_rooms_count
        self.grid = np.full((self.grid_width, self.grid_height), WALL_TILE, dtype=int)
        for r in self.maze_rooms:
            self.grid[r.left:r.right, r.top:r.bottom] = WALKABLE_TILE

    def check_rooms_are_adjacent_to_make_a_door(self, room1, room2):
        if not room1.colliderect(room2):
            return False
        wall = get_rect_intersection(room1, room2)
        wall_square = wall.width * wall.height
        return self.wall_can_contain_a_door(wall_square)

    def _find_adjacent_rooms(self):
        rooms_with_walls = list(get_room_rect_with_walls(r) for r in self.maze_rooms)
        self.adjacent_rooms = defaultdict(set)
        for i in range(0, len(rooms_with_walls)):
            for k in range(i + 1, len(rooms_with_walls)):
                if self.check_rooms_are_adjacent_to_make_a_door(rooms_with_walls[i], rooms_with_walls[k]):
                    self.adjacent_rooms[i].add(k)
                    self.adjacent_rooms[k].add(i)

    def get_all_paths_using_bfs(self, start, end):
        todo = [[start, [start]]]
        while 0 < len(todo):
            (node, path) = todo.pop(0)
            for next_node in self.adjacent_rooms[node]:
                if next_node in path:
                    continue
                elif next_node == end:
                    yield path + [next_node]
                else:
                    todo.append([next_node, path + [next_node]])

    def _make_door(self, room1, room2, walkable_tile=WALKABLE_TILE):
        wall = get_rect_intersection(room1, room2)
        wall_square = wall.width * wall.height
        if not self.wall_can_contain_a_door(wall_square):
            self.logger.error("the wall is too short(length={}) to create a door of size {}".format(wall_square, self.door_width))
            random_start = 1
        else:
            random_start = random.randint(1,  wall_square - self.door_width - 1)
        cnt = 0
        current_door_width = 0
        for x in range(wall.left, wall.right):
            for y in range(wall.top, wall.bottom):
                if cnt >= random_start and current_door_width < self.door_width:
                    current_door_width += 1
                    self.grid[x, y] = walkable_tile
                cnt += 1

    def _build_path_to_exit(self, start_room_index):
        paths = list(self.get_all_paths_using_bfs(start_room_index, self.exit_room_index))
        try:
            longest_path = max(paths, key=lambda x: len(x))
        except Exception as exp:
            retry = list(self.get_all_paths_using_bfs(start_room_index, self.exit_room_index))
            raise
        for opened_room_index in range(0, len(longest_path)):
            if self.room_to_doors[longest_path[opened_room_index]] > 0:
                break

        for i in range(opened_room_index):
            room_index1 = longest_path[i]
            room_index2 = longest_path[i + 1]
            r1 = get_room_rect_with_walls(self.maze_rooms[room_index1])
            r2 = get_room_rect_with_walls(self.maze_rooms[room_index2])
            self.room_to_doors[room_index1] += 1
            self.room_to_doors[room_index2] += 1
            self._make_door(r1, r2)

    def open_closed_rooms(self):
        for room_index, room in enumerate(self.maze_rooms):
            if self.room_to_doors[room_index] == 0 and room_index != self.exit_room_index:
                self._build_path_to_exit(room_index)
    def check_wall(self, x, y):
        return x == self.grid_width or y == self.grid_height or self.grid[x][y] == WALL_TILE

    def check_dead_top_left_corner(self, rect: pygame.Rect):
        return self.check_wall(rect.left - 1, rect.top) and self.check_wall(rect.left, rect.top - 1)
    def check_dead_top_right_corner(self, rect: pygame.Rect):
        return self.check_wall(rect.right + 1, rect.top) and self.check_wall(rect.right, rect.top - 1)
    def check_dead_bottom_left_corner(self, rect: pygame.Rect):
        return self.check_wall(rect.left - 1, rect.bottom) and self.check_wall(rect.left, rect.bottom + 1)
    def check_dead_bottom_right_corner(self, rect: pygame.Rect):
        return self.check_wall(rect.right + 1, rect.bottom) and self.check_wall(rect.right, rect.bottom + 1)

    def _build_start(self):
        self.start_room_index = random.randint(0, self.inner_rooms_count - 1)
        self.start_pos = self.maze_rooms[self.start_room_index].center

    def generate_dead_room_corners(self, room_index):
        rect: pygame.Rect
        rect = self.maze_rooms[room_index]
        if self.check_dead_top_left_corner(rect):
            yield Vector2(rect.topleft) + (1, 1)
        if self.check_dead_top_right_corner(rect):
            yield Vector2(rect.topright) + (-3, 1)
        if self.check_dead_bottom_left_corner(rect):
            yield Vector2(rect.bottomleft) + (1, -3)
        if self.check_dead_bottom_right_corner(rect):
            yield Vector2(rect.bottomright) + (-4, -3)

    def _build_possible_locations(self):
        self.room_places = list()
        for i in range(len(self.maze_rooms)):
            for coord in self.generate_dead_room_corners(i):
                self.room_places.append(TRoomPlace(self, i, coord))
            self.room_places.append(TRoomPlace(self, i, self.maze_rooms[i].center, "center_place"))

    def get_main_walls(self):
        return [pygame.Rect(0,  0, self.grid_width, 1),
                pygame.Rect(0,  0,  1, self.grid_height),
                pygame.Rect(0, self.grid_height - 1, self.grid_width, 1),
                pygame.Rect(self.grid_width - 1, 0,  1, self.grid_height)]

    def _build_exit(self):
        rooms_with_walls = list(get_room_rect_with_walls(r) for r in self.maze_rooms)
        main_walls = self.get_main_walls()
        random.shuffle(main_walls)
        for w in main_walls:
            for i in range(0, len(rooms_with_walls)):
                if w.colliderect(rooms_with_walls[i]):
                    if i != self.start_room_index:
                        self.exit_room_index = i
                        self._make_door(rooms_with_walls[i], w, TARGET_TILE)
                        return

    def generate_maze(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.room_to_doors.clear()
        self._generate_rooms()
        self._build_start()
        self._build_exit()
        self._find_adjacent_rooms()
        self._build_path_to_exit(self.start_room_index)
        self._build_possible_locations()

