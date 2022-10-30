import pygame
from logging_wrapper import setup_logging

def init_joystick(logger):
    pygame.joystick.init()
    logger.info("joysticks count = {}".format(pygame.joystick.get_count()))
    if not pygame.joystick.get_init() or pygame.joystick.get_count() < 1:
        logger.error("cannot find joystick")
        return None
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    if not joystick.get_init():
        logger.error("cannot init joystick")
        return None
    logger.info("joystick name = {}".format(joystick.get_name()))
    logger.info("joystick axes count = {}".format(joystick.get_numaxes()))
    logger.info("joystick get_numballs = {}".format(joystick.get_numballs()))
    logger.info("joystick get_numbuttons = {}".format(joystick.get_numbuttons()))
    return joystick


if __name__ == "__main__":
    logger = setup_logging("test_joystick")
    wheel = init_joystick(logger)
