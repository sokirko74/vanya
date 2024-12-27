# 1. install https://github.com/umer0586/SensorServer on android
# 2. update ip in this script
# 2. pip install python-uinput
# 3. run as a root or sudo chmod +0666 /dev/uinput (safety problem)

import websocket
import json
import time
import uinput
from utils.uinput_wrapper import KeyControls


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