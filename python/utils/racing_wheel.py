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

    def __init__(self, logger, center, level=120, sound_pedals=False, angle_level_ratio=30):
        self.logger = logger
        self.raw_angle = None
        self.center = center
        self.level = level
        self.pressed_buttons = set()
        self.last_left_hat_button_time = 0
        self.right_button_time = 0
        self.sound_pedals = sound_pedals
        self.device = None
        self.angle_level_ratio = angle_level_ratio
        self.init_device()

    def init_device(self):
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

    def read_one_event(self):
        if self.is_attached():
            for i in range(3):
                try:
                    return self.device.read_one()
                except (OSError, AttributeError) as exp:
                    self.logger.error(type(exp))
                    self.logger.error('wait 0.3 and try initialize one more time')
                    time.sleep(0.3)
                    self.init_device()

    def read_events(self):
        event = self.read_one_event()

        while event is not None:
            #print(event)
            if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_HAT0X or event.code == ecodes.ABS_HAT0Y:
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
                tm = time.time()
                if tm - self.right_button_time > 3:
                    self.right_button_time = tm
                    self.logger.info("right_button")
                    self.pressed_buttons.add(TRacingWheel.right_button)
            elif event.code == TRacingWheel.left_pedal:
                if event.value > self.level:
                    self.logger.info("left pedal")
                    self.pressed_buttons.add(TRacingWheel.left_pedal)
                    if self.sound_pedals:
                        print ("aaaasss")
                        pygame.mixer.music.load('beeps/nolik.wav')
                        pygame.mixer.music.play()
                else:
                    if TRacingWheel.left_pedal in self.pressed_buttons:
                        self.pressed_buttons.remove(TRacingWheel.left_pedal)
                #self.logger.info("left_pedal value={} {}".format(event.value, self.pressed_buttons))
            elif event.code == TRacingWheel.right_pedal:
                if event.value > self.level:
                    self.logger.info("right_pedal")
                    self.pressed_buttons.add(TRacingWheel.right_pedal)
                    if self.sound_pedals:
                        print ("aaaasss")
                        pygame.mixer.music.load('beeps/krestik.wav')
                        pygame.mixer.music.play()
                else:
                    if TRacingWheel.right_pedal in self.pressed_buttons:
                        self.pressed_buttons.remove(TRacingWheel.right_pedal)
                #self.logger.info("right_pedal value={} {}".format(event.value, self.pressed_buttons))
            event = self.read_one_event()

    def is_left_pedal_pressed(self):
        return TRacingWheel.left_pedal in self.pressed_buttons

    def is_right_pedal_pressed(self):
        return TRacingWheel.right_pedal in self.pressed_buttons

    def get_angle(self):
        self.read_events()
        if self.raw_angle is not None:
            return int((self.raw_angle - self.center) / self.angle_level_ratio)

    def test(self):
        run = True
        self.sound_pedals = True
        self.level = 30
        print("aaa")
        pygame.display.init()
        pygame.mixer.init()
        while run:
            self.read_events()
            #   print ("aaa")
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.K_ESCAPE:
                    run = False
            time.sleep(0.2)
            pygame.event.pump()


if __name__ == "__main__":
    logger = setup_logging("test_wheel")
    wheel = TRacingWheel(logger, 1000, sound_pedals=True)
    wheel.test()