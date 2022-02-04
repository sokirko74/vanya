from utils.colors import TColors
from utils.racing_wheel import TRacingWheel
import pygame


class TGameIntro:
    exit_game_action = 1
    start_game_action = 2

    def __init__(self, screen, background_image_path, racing_wheel: TRacingWheel):
        self.screen = screen
        self.racing_wheel = racing_wheel
        self.action = None
        self.image = pygame.transform.scale(pygame.image.load(background_image_path),
                                   (self.screen.get_width(), self.screen.get_height()))

    def message(self, mess, colour, size, x, y):
        font = pygame.font.SysFont(None, size)
        screen_text = font.render(mess, True, colour)
        self.screen.blit(screen_text, (x, y))
        pygame.display.update()

    def insert_button(self, x, y, w, h, mess, mess_color, actc, noc, size, tx, ty, func):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x + w > mouse[0] > x and y + h > mouse[1] > y:
            pygame.draw.rect(self.screen, actc, [x, y, w, h])
            self.message(mess, mess_color, size, tx, ty)
            pygame.display.update()
            if click == (1, 0, 0):
                func()
        else:
            pygame.draw.rect(self.screen, noc, [x, y, w, h])
            self.message(mess, mess_color, size, tx, ty)
            pygame.display.update()
        pygame.display.update()

    def draw_intro_button(self, x, y, message, color, func):
        self.insert_button(x, y, 70, 30, message, TColors.white, color, TColors.red, 25, x + 6,
                      y + 6, func)

    def set_exit_action(self):
        self.action = TGameIntro.exit_game_action

    def set_start_game_action(self):
        self.action = TGameIntro.start_game_action

    def get_next_action(self, prev_score=None):
        self.screen.blit(self.image, (0, 0))
        pygame.display.update()
        self.action = None
        while self.action is None:
            self.racing_wheel.forget_buttons()
            self.racing_wheel.read_events()
            if TRacingWheel.left_button in self.racing_wheel.pressed_buttons:
                self.action = TGameIntro.start_game_action
                break
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.action = TGameIntro.exit_game_action
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.racing_wheel.save_wheel_center()
                    if event.key == pygame.K_RETURN:
                        self.action = TGameIntro.start_game_action
                    if event.key == pygame.K_ESCAPE:
                        self.action = TGameIntro.exit_game_action
                        break

            if prev_score is not None:
                self.message("Очки: {}".format(prev_score), TColors.black, 250, 100, 100)
            button_y = 300
            self.draw_intro_button(200, button_y, 'GO!', TColors.bright_red, self.set_start_game_action )
            self.draw_intro_button(self.screen.get_width() - 200, button_y, 'QUIT', TColors.bright_green, self.set_exit_action)
            pygame.display.update()

        pygame.display.update()
