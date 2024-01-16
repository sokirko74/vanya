from utils.colors import TColors
from utils.racing_wheel import TRacingWheel
from utils.pygame_button import PygameButton

import pygame
import time


class TGameIntro:
    exit_game_action = 1
    start_game_action = 2

    def __init__(self, screen, background_image_path, racing_wheel: TRacingWheel):
        self.screen = screen
        self.racing_wheel = racing_wheel
        self.action = None
        self.image = pygame.transform.scale(pygame.image.load(background_image_path),
                                   (self.screen.get_width(), self.screen.get_height()))
        button_y = 300
        width = 100
        height = 50
        self.go_button = PygameButton(self.screen, 200, button_y, width, height, text='GO!', on_click=self.set_start_game_action)
        self.exit_button = PygameButton(self.screen, self.screen.get_width() - 200, button_y, width, height,
                                        text='QUIT', on_click=self.set_exit_action)

    def message(self, mess, colour, size, x, y):
        font = pygame.font.SysFont(None, size)
        screen_text = font.render(mess, True, colour)
        self.screen.blit(screen_text, (x, y))
        pygame.display.update()

    def set_exit_action(self):
        self.action = TGameIntro.exit_game_action

    def set_start_game_action(self):
        self.action = TGameIntro.start_game_action

    def get_next_action(self, message_text=None):
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

            if message_text is not None:
                self.message(message_text, TColors.black, 250, 100, 100)
            self.go_button.process()
            self.exit_button.process()
            pygame.display.update()
            time.sleep(0.2)
