from evdev import list_devices, InputDevice, ecodes
from utils.logging_wrapper import setup_logging
import pygame
import time


class TRacingWheel:
    left_button = 295
    right_button = 294
    left_pedal = 10
    right_pedal = 9
    left_hat_button = 17

    def __init__(self, logger, center):
        self.logger = logger
        self.raw_angle = None
        self.center = center
        self.pressed_buttons = set()
        self.last_left_hat_button_time = 0
        joysticks = list_devices()
        if len(joysticks) > 0:
            self.device = InputDevice(joysticks[0])
            self.read_events()
        else:
            self.logger.error("no racing wheel found")
            self.device = None

    def save_wheel_center(self):
        if self.raw_angle is not None:
            self.logger.info("set wheel center to {}".format(self.raw_angle))
            self.center = self.raw_angle

    def forget_buttons(self):
        self.pressed_buttons.clear()

    def is_attached(self):
        return self.device is not None

    def read_events(self):
        if self.device is None:
            return
        event = self.device.read_one()
        while event is not None:
            if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_HAT0X or event.code == ecodes.ABS_HAT0Y:
                tm = time.time()
                if tm - self.last_left_hat_button_time > 6:
                    self.last_left_hat_button_time = tm
                    self.logger.info("left_hat_button event.code={}, time={}".format(event.code, tm))
                    self.pressed_buttons.add(TRacingWheel.left_hat_button)
            elif event.code == ecodes.ABS_WHEEL:
                self.raw_angle = event.value
                #self.logger.info("abs_wheel value={}, center={}".format(self.raw_angle, self.center))
            if event.code == TRacingWheel.left_button:
                self.logger.debug("left_button")
                self.pressed_buttons.add(TRacingWheel.left_button)
            elif event.code == TRacingWheel.right_button:
                self.logger.debug("right_button")
                self.pressed_buttons.add(TRacingWheel.right_button)
            elif event.code == TRacingWheel.left_pedal:
                if event.value > 120:
                    self.pressed_buttons.add(TRacingWheel.left_pedal)
                else:
                    if TRacingWheel.left_pedal in self.pressed_buttons:
                        self.pressed_buttons.remove(TRacingWheel.left_pedal)
                #self.logger.info("left_pedal value={} {}".format(event.value, self.pressed_buttons))
            elif event.code == TRacingWheel.right_pedal:
                self.logger.debug("right_pedal")
                if event.value > 120:
                    self.pressed_buttons.add(TRacingWheel.right_pedal)
                else:
                    if TRacingWheel.right_pedal in self.pressed_buttons:
                        self.pressed_buttons.remove(TRacingWheel.right_pedal)
                #self.logger.info("right_pedal value={} {}".format(event.value, self.pressed_buttons))
            event = self.device.read_one()

    def is_left_pedal_pressed(self):
        return TRacingWheel.left_pedal in self.pressed_buttons

    def is_right_pedal_pressed(self):
        return TRacingWheel.right_pedal in self.pressed_buttons

    def get_angle(self):
        self.read_events()
        if self.raw_angle is not None:
            return int((self.raw_angle - self.center) / 50)

    def test(self):
        run = False
        while run:
            self.process_wheel_pedals()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.K_ESCAPE:
                    run = False
            time.sleep(0.2)
            pygame.event.pump()


if __name__ == "__main__":
    logger = setup_logging("test_wheel")
    wheel = TRacingWheel(logger, 1000)
    wheel.test()