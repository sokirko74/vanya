import utils.maze_generator as generator
from utils.colors import TColors
import pygame
from pygame.math import Vector2


ColorMap = {
    generator.WALKABLE_TILE: TColors.white,
    generator.WALL_TILE: TColors.red,
    generator.TARGET_TILE: TColors.green,
}


class TTile(pygame.sprite.Sprite):
    def __init__(self, parent, pos, tile_type=-1, color=TColors.black):
        pygame.sprite.Sprite.__init__(self)
        self.parent = parent
        if tile_type in ColorMap:
            color = ColorMap[tile_type]
        self.tile_type = tile_type
        self.image = pygame.Surface((self.parent.block_size, self.parent.block_size))
        self.wall = False
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = Vector2(self.parent.maze_rect.topleft) + pos

    def draw(self):
        self.parent.screen.blit(self.image, self.rect)
