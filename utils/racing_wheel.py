from evdev import list_devices, InputDevice, ecodes, InputEvent, KeyEvent
from utils.logging_wrapper import setup_logging
import pygame
import time
from collections import  defaultdict


class TRacingWheel:
    right_button = 294
    left_button = 295
    right_under_wheel_button = 336
    right_pedal = 9
    left_pedal = 10
    left_hat_button_x = ecodes.ABS_HAT0X
    left_hat_button_y = ecodes.ABS_HAT0Y
    right_hat_button_x = 298
    right_hat_button_y = 299

    def __init__(self, logger, center, left_level=120, sound_pedals=False, angle_level_ratio=30):
        self.logger = logger
        self.raw_angle = None
        self.center = center
        self.left_level = left_level
        self.pressed_buttons = set()
        self.last_press_times = defaultdict(int)
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
            self.read_wheel_events()
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

    def _key_is_pressed(self, event: InputEvent, key_code):
        check_type = event.type == ecodes.EV_ABS or event.type == ecodes.EV_KEY
        check_down = event.value != 0
        #print(event)

        if check_type and (event.code == key_code) and check_down:
            #tm = time.time()
            tm = event.sec
            last_time = self.last_press_times[key_code]
            if tm - last_time > 4:
                self.logger.debug('last time={} , time ={}'.format(last_time, tm))
                self.last_press_times[key_code] = tm
                return True
        return False

    def _key_is_up(self, event: InputEvent, key_code):
        if key_code in self.pressed_buttons:
            check_type = event.type == ecodes.EV_ABS or event.type == ecodes.EV_KEY
            check_up = event.value == 0
            return check_type and (event.code == key_code) and check_up
        else:
            return False

    def _left_hat_is_pressed(self, event):
        return self._key_is_pressed(event, TRacingWheel.left_hat_button_x) or \
            self._key_is_pressed(event, TRacingWheel.left_hat_button_y)

    def left_hat_was_pressed(self):
        for k in [TRacingWheel.left_hat_button_x, TRacingWheel.left_hat_button_y]:
            if k in self.pressed_buttons:
                self.pressed_buttons.remove(k)
                return True
        return False

    def right_hat_was_pressed(self):
        for k in [TRacingWheel.right_hat_button_x, TRacingWheel.right_hat_button_y]:
            if k in self.pressed_buttons:
                self.pressed_buttons.remove(k)
                return True
        return False

    def _right_hat_is_pressed(self, event):
        return self._key_is_pressed(event, TRacingWheel.right_hat_button_x) or \
        self._key_is_pressed(event, TRacingWheel.right_hat_button_y)

    def _left_small_button_is_pressed(self, event):
        return self._key_is_pressed(event, TRacingWheel.left_button)

    def _right_under_wheel_button_is_pressed(self, event):
        return self._key_is_pressed(event, TRacingWheel.right_under_wheel_button)

    def _right_small_button_is_pressed(self, event):
        return self._key_is_pressed(event, TRacingWheel.right_button)

    def read_wheel_events(self):
        event = self.read_one_event()

        while event is not None:
            #if event.code != 0:
            #    self.logger.info("{}".format(event))
            if self._left_hat_is_pressed(event):
                self.logger.info("left_hat_button event.code={}".format(event.code))
                self.pressed_buttons.add(TRacingWheel.left_hat_button_x)
            elif self._right_hat_is_pressed(event):
                self.logger.info("right_hat_button event.code={} time={}".format(
                    event.code, event.sec))
                self.pressed_buttons.add(TRacingWheel.right_hat_button_x)
            elif event.code == ecodes.ABS_WHEEL:
                self.raw_angle = event.value
                #self.logger.info("abs_wheel value={}, center={}".format(self.raw_angle, self.center))
            if  self._right_under_wheel_button_is_pressed(event):
                self.logger.info("right under wheel button is pressed")
                self.pressed_buttons.add(TRacingWheel.right_under_wheel_button)
            elif self._left_small_button_is_pressed(event):
                self.logger.info("left small button is pressed")
                self.pressed_buttons.add(TRacingWheel.left_button)
            elif self._key_is_up(event, TRacingWheel.left_button):
                self.pressed_buttons.remove(TRacingWheel.left_button)
            elif self._right_small_button_is_pressed(event):
                self.logger.info("right small button is pressed")
                self.pressed_buttons.add(TRacingWheel.right_button)
            elif event.code == TRacingWheel.left_pedal:
                if event.value > self.left_level:
                    self.logger.info("left pedal {}".format(event.value))
                    self.pressed_buttons.add(TRacingWheel.left_pedal)
                else:
                    self.forget_key(TRacingWheel.left_pedal)
                #self.logger.info("left_pedal value={} {} level={}".format(event.value, self.pressed_buttons, self.left_level))
            elif event.code == TRacingWheel.right_pedal:
                if event.value > 70:
                    self.logger.info("right_pedal: {}".format(event.value))
                    self.pressed_buttons.add(TRacingWheel.right_pedal)
                else:
                    self.forget_key(TRacingWheel.right_pedal)
                #self.logger.info("right_pedal value={} {}".format(event.value, self.pressed_buttons))
            event = self.read_one_event()

    def is_left_pedal_pressed(self):
        return TRacingWheel.left_pedal in self.pressed_buttons

    def is_right_pedal_pressed(self):
        return TRacingWheel.right_pedal in self.pressed_buttons

    def forget_key(self, key):
        if key in self.pressed_buttons:
            self.pressed_buttons.remove(key)

    def get_wheel_angle(self):
        if self.raw_angle is not None:
            return int((self.raw_angle - self.center) / self.angle_level_ratio)

    def test(self):
        run = True
        self.sound_pedals = True
        self.level = 40
        print("aaa")
        pygame.display.init()
        pygame.mixer.init()
        while run:
            self.read_wheel_events()
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
