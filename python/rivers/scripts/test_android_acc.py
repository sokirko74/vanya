# 1. install https://github.com/umer0586/SensorServer on android
# 2. update ip in this script
# 2. pip install python-uinput
# 3. run as a root or sudo chmod +0666 /dev/uinput (safety problem)

import websocket
import json
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


KEYBOARD = KeyControls()


def on_message(ws, message):
    global KEYBOARD
    values = json.loads(message)['values']
    x = values[0]
    y = values[1]
    z = values[2]
    threshold = 2
    if z > threshold:
        KEYBOARD.press_up()
    elif z < -threshold:
        KEYBOARD.press_down()
    else:
        KEYBOARD.unpress_up_and_down()

    if x > threshold:
        KEYBOARD.press_left()
    elif x < -threshold:
        KEYBOARD.press_right()
    else:
        KEYBOARD.unpress_left_and_right()


def on_error(ws, error):
    print("error occurred ", error)


def on_close(ws, close_code, reason):
    print("connection closed : ", reason)


def on_open(ws):
    print("connected")

def connect(url):
    ws = websocket.WebSocketApp(url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()



def main():
    connect("ws://192.168.100.107:8080/sensor/connect?type=android.sensor.accelerometer")

if __name__ == "__main__":
    main()