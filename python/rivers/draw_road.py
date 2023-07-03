from python.utils.colors import TColors
import math
import pygame


def draw_road_line(screen, x1, y1, x2, y2, colr, width=1):
    D = 50
    if x2 == x1:
        pygame.draw.line(screen, colr,
                         (x1, y1),
                         (x2, y2), width=width)
        return
    alpha = math.atan((y2-y1-2*D) / abs(x2-x1))
    alpha1 = math.atan((y2 - y1 - 2 * (D+2*width)) / abs(x2 - x1))
    alpha_2 = (math.pi/2 - alpha) / 2
    R = D / math.tan(alpha_2)

    if x1 < x2:
        start_angle = 0
        sign = 1
        rct1 = pygame.Rect(x2 - 2*R, y2-R, 2*R, 2*R )
        rct2 = pygame.Rect(x1, y1 - R, 2 * R, 2 * R)
    else:
        sign = -1
        start_angle = math.pi / 2 + alpha
        rct1 = pygame.Rect(x2, y2 - R, 2 * R, 2 * R)
        rct2 = pygame.Rect(x1 - 2*R, y1 - R, 2 * R, 2 * R)
    stop_angle = start_angle + math.pi/2 - alpha
    pygame.draw.arc(screen, colr, rct1, width=width, start_angle=start_angle, stop_angle=stop_angle)
    pygame.draw.arc(screen, colr, rct2, width=width, start_angle=start_angle + math.pi, stop_angle=stop_angle+math.pi)
    pygame.draw.line(screen, colr,
                     (x1 + sign * math.cos(alpha)*D, y1 + D + math.sin(alpha1) * D),
                     (x2 - sign * math.cos(alpha)*D, y2 - D - math.sin(alpha1) * D),
                     width=width)


def draw_road(screen, x1, y1, x2, y2, colr=TColors.white,  width=30):
    for i in range(width):
        draw_road_line(screen, x1+i, y1, x2+i, y2, colr, width=1)


if __name__ == "__main__":
    clock = pygame.time.Clock()
    pygame.display.init()
    width = 800
    height = 400
    screen = pygame.display.set_mode((640, 480))

    y1 = 50
    y2 = 350

    pygame.draw.line(screen, TColors.white, (0, y1), (width, y1))
    pygame.draw.line(screen, TColors.white, (0, y2), (width, y2))
    draw_road(screen, 100, y1, 500, y2)

    draw_road(screen, 500, y1, 100, y2)
    draw_road(screen, 250, y1, 250, y2)
    draw_road(screen, 600, y1, 450, y2)

    pygame.display.update()

    game_over = False
    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_over = True
                    break
    pygame.quit()

