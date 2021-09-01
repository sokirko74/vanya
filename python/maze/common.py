import pygame
import math


class TMazeCommon:

    @staticmethod
    def add_tuples(a, b):
        return a[0] + b[0], a[1] + b[1]

    @staticmethod
    def circle_collidelist(center, r, rec_ls):
        for i in range(len(rec_ls)):
            circle_distance_x = abs(center[0] - rec_ls[i].centerx)
            circle_distance_y = abs(center[1] - rec_ls[i].centery)
            if circle_distance_x > rec_ls[i].w / 2.0 + r or circle_distance_y > rec_ls[i].h / 2.0 + r:
                continue
            if circle_distance_x <= rec_ls[i].w / 2.0 or circle_distance_y <= rec_ls[i].h / 2.0:
                return i
        return -1

    @staticmethod
    def rect_collide_list(rect, obstacles):
        for index, obstacle in enumerate(obstacles):
            if rect.colliderect(obstacle):
                return index
        return -1

    @staticmethod
    def rotate_point(pt, angle):
        x = pt[1] * math.cos(math.radians(angle)) + pt[0] * math.sin(math.radians(angle))
        y = pt[0] * math.cos(math.radians(angle)) - pt[1] * math.sin(math.radians(angle))
        return x, y

    @staticmethod
    def rotate_shape(pt_ls, angle):
        res = []
        s = math.sin(math.radians(angle))
        c = math.cos(math.radians(angle))
        for pt in pt_ls:
            x = pt[1] * c + pt[0] * s
            y = pt[0] * c - pt[1] * s
            res.append((x, y))
        return res

    @staticmethod
    def rot_center(image, rect, angle):
        c = rect.center
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = rot_image.get_rect()
        rot_rect.center = c
        return rot_image, rot_rect

