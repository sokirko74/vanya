import pygame, sys, gif_pygame

win = pygame.display.set_mode((512, 512))
example_gif = gif_pygame.load("example.gif")  # Loads a .gif file

clock = pygame.Clock()

while True:
    clock.tick(60)
    win.fill((0, 0, 0))

    example_gif.render(win, (128 - example_gif.get_width() * 0.5, 256 - example_gif.get_height() * 0.5))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit();
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if example_gif.paused:  # Check whether `example_gif` is paused or not
                    example_gif.unpause()  # unpauses `example_gif` if it was paused
                else:
                    example_gif.pause()  # pauses `example_gif` if it was unpaused

                #if example_surfs.paused:  # Check whether `example_surfs` is paused or not
                #    example_surfs.unpause()  # unpauses `example_surfs` if it was paused
                #else:
                #    example_surfs.pause()  # pauses `example_surfs` if it was unpaused

    pygame.display.flip()