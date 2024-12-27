import pygame
class PygameButton:
    def __init__(self, screen, x, y, width, height, text='Button', on_click=None, one_press=False):
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.on_click_function = on_click
        self.onePress = one_press

        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }

        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        font = pygame.font.SysFont('Arial', 40)
        self.buttonSurf = font.render(text, True, (20, 20, 20))

        self.alreadyPressed = False

    def process(self):

        mouse_pos = pygame.mouse.get_pos()

        self.buttonSurface.fill(self.fillColors['normal'])
        if self.buttonRect.collidepoint(mouse_pos):
            self.buttonSurface.fill(self.fillColors['hover'])

            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.fillColors['pressed'])

                if self.onePress:
                    self.on_click_function()

                elif not self.alreadyPressed:
                    self.on_click_function()
                    self.alreadyPressed = True

            else:
                self.alreadyPressed = False

        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width / 2 - self.buttonSurf.get_rect().width / 2,
            self.buttonRect.height / 2 - self.buttonSurf.get_rect().height / 2
        ])
        self.screen.blit(self.buttonSurface, self.buttonRect)