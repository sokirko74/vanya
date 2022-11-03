import time
import uinput
import os
import sys
import argparse
from evdev import list_devices, InputDevice, ecodes

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel

def switch_chrome():
    os.system('wmctrl -v  -a Chrome')
    time.sleep(0.1)


#!!! to https://stackoverflow.com/questions/11939255/writing-to-dev-uinput-on-ubuntu-12-04
# sudo chmod +0666 /dev/uinput

class TPedalState:
    forward = "forward"
    backward = "backward"
    no_change = "no_change"

class TCrazeDriftWrapper:
    def __init__(self, args):
        self.logger = setup_logging("crazy_drifter")
        self.game_over = False
        self.virtual_keyboard = uinput.Device([
                uinput.KEY_UP,
                uinput.KEY_DOWN,
                uinput.KEY_LEFT,
                uinput.KEY_RIGHT,
                uinput.KEY_W,
                uinput.KEY_S,
                ],
                bustype=3 # USB

        )
        time.sleep(1)
        joysticks = list_devices()
        assert len(joysticks) > 0
        self.racing_wheel = InputDevice(joysticks[0])
        self.wheel_center = args.wheel_center
        self.wheel_angle_long_press_level = 800
        self.wheel_angle_short_press_level = 200
        self.pedal_level = 90
        self.pedal_state = TPedalState.no_change
        self.pressed_buttons = set()

    def press_virtual_button(self, btn):
        if btn not in self.pressed_buttons:
            self.logger.info("press {}".format(btn))
            self.virtual_keyboard.emit(btn, 1)
            self.pressed_buttons.add(btn)

    def click_virtual_button(self, btn):
        self.logger.info("click {}".format(btn))
        self.virtual_keyboard.emit_click(btn)

    def unpress_virtual_button(self, btn):
        if btn in self.pressed_buttons:
            self.logger.info("unpress {}".format(btn))
            self.virtual_keyboard.emit(btn, 0)
            self.pressed_buttons.remove(btn)

    def click_short(self, key):
        self.press_virtual_button(key)
        time.sleep(0.1)
        self.unpress_virtual_button(key)

    def process_angle(self, angle):
        print ("angle={}".format(angle))
        if abs(angle - self.wheel_center) < self.wheel_angle_short_press_level:
            self.logger.info("direct")
            self.unpress_virtual_button(uinput.KEY_LEFT)
            self.unpress_virtual_button(uinput.KEY_RIGHT)
        elif angle < self.wheel_center - self.wheel_angle_long_press_level:
            self.logger.info("long left={}".format(angle))
            self.unpress_virtual_button(uinput.KEY_RIGHT)
            self.press_virtual_button(uinput.KEY_LEFT)
        elif angle > self.wheel_center + self.wheel_angle_long_press_level:
            self.logger.info("long right={}".format(angle))
            self.unpress_virtual_button(uinput.KEY_LEFT)
            self.press_virtual_button(uinput.KEY_RIGHT)
        elif angle < self.wheel_center - self.wheel_angle_short_press_level:
            self.logger.info("short left={}".format(angle))
            self.click_short(uinput.KEY_LEFT)
        elif angle > self.wheel_center + self.wheel_angle_short_press_level:
            self.logger.info("short right={}".format(angle))
            self.click_short(uinput.KEY_RIGHT)

    def process_pedals(self, left_pedal_value, right_pedal_value):
        if left_pedal_value is None and right_pedal_value is None:
            return
        if left_pedal_value is None:
            left_pedal_value = 0
        if right_pedal_value is None:
            right_pedal_value = 0
        #print('pedal  left_pedal_value: {}, right_pedal_value={}'.format(
        #    left_pedal_value, right_pedal_value))
        new_state = TPedalState.no_change
        if left_pedal_value > right_pedal_value and left_pedal_value > self.pedal_level:
            new_state = TPedalState.backward
        elif right_pedal_value > left_pedal_value and right_pedal_value > self.pedal_level:
            new_state = TPedalState.forward

        if self.pedal_state != new_state:

            print('pedal state: {}->{}'.format(self.pedal_state, new_state))
            motion2key = {
                 TPedalState.forward: uinput.KEY_UP,
                 TPedalState.backward: uinput.KEY_DOWN
            }
            # motion2key = {
            #     TPedalState.forward: uinput.KEY_W,
            #     TPedalState.backward: uinput.KEY_S
            # }
            self.pedal_state = new_state
            for key in motion2key.values():
                self.unpress_virtual_button(key)
            if self.pedal_state in motion2key:
                self.press_virtual_button(motion2key[self.pedal_state])
                #self.click_virtual_button(motion2key[self.pedal_state])


    def game_loop(self):
        while not self.game_over:
            event = self.racing_wheel.read_one()
            left_pedal_value = None
            right_pedal_value = None
            while event is not None:

                if event.code == ecodes.ABS_WHEEL:
                    self.process_angle(event.value)
                elif event.code == TRacingWheel.left_pedal:
                    #print(event)
                    left_pedal_value = event.value
                elif event.code == TRacingWheel.right_pedal:
                    right_pedal_value = event.value
                event = self.racing_wheel.read_one()
            self.process_pedals(left_pedal_value, right_pedal_value)
            time.sleep(0.1)

    def run(self):
        switch_chrome()
        self.game_loop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", dest='silent', default=False, action="store_true")
    parser.add_argument("--wheel-center", dest='wheel_center', default=100, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    game = TCrazeDriftWrapper(args)
    game.run()





# with uinput.UInput() as ui:
#     for i in range (10):
#         ui.write(e.EV_KEY, e.   KEY_E, 1)
#         time.sleep(0.2)
#         ui.write(e.EV_KEY, e.KEY_E, 0)
#         time.sleep(0.2)
#         ui.syn()