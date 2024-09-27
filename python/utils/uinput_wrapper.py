import time

import uinput

class KeyControls:
    def __init__(self):
        self.pressed_keys = set()
        self.device = uinput.Device([
            uinput.KEY_UP,
            uinput.KEY_DOWN,
            uinput.KEY_LEFT,
            uinput.KEY_RIGHT,
            uinput.KEY_ENTER,
            uinput.KEY_TAB,
            uinput.BTN_LEFT,
        ])

    def __del__(self):
        self.device.destroy()

    def press_key(self, key):
        if key not in self.pressed_keys:
            print ("press {}".format(key))
            self.device.emit(key, 1)
            self.pressed_keys.add(key)

    def unpress_key(self, key):
        if key in self.pressed_keys:
            print ("unpress {}".format(key))
            self.device.emit(key, 0)
            self.pressed_keys.remove(key)

    def press_down(self):
        self.unpress_key(uinput.KEY_UP)
        self.press_key(uinput.KEY_DOWN)

    def press_up(self):
        self.unpress_key(uinput.KEY_DOWN)
        self.press_key(uinput.KEY_UP)

    def unpress_up_and_down(self):
        self.unpress_key(uinput.KEY_DOWN)
        self.unpress_key(uinput.KEY_UP)

    def press_left(self):
        self.unpress_key(uinput.KEY_RIGHT)
        self.press_key(uinput.KEY_LEFT)

    def press_right(self):
        self.unpress_key(uinput.KEY_LEFT)
        self.press_key(uinput.KEY_RIGHT)

    def unpress_left_and_right(self):
        self.unpress_key(uinput.KEY_LEFT)
        self.unpress_key(uinput.KEY_RIGHT)

    def _press_and_release(self, key):
        self.device.emit(key, 1)
        time.sleep(0.2)
        self.device.emit(key, 0)

    def press_tab(self):
        self._press_and_release(uinput.KEY_TAB)

    def press_enter(self):
        self._press_and_release(uinput.KEY_TAB)

    def click_left(self):
        self._press_and_release(uinput.uinput.BTN_LEFT)
