from utils.racing_wheel import TRacingWheel
import time
from utils.logging_wrapper import setup_logging


import uinput

def main():
    logger = setup_logging("test_wheel")
    wheel = TRacingWheel(logger, -30, sound_pedals=False)
    center_angle = -30
    print("center_angle  {}".format(center_angle))
    keys = [uinput.KEY_UP,
    uinput.KEY_DOWN, uinput.KEY_LEFT, uinput.KEY_RIGHT, uinput.KEY_TAB]
    with uinput.Device(keys) as device:
        while True:
            wheel.read_events()
            if wheel.is_right_pedal_pressed():
                print("up")
                device.emit(uinput.KEY_UP, 1)
            elif wheel.is_right_pedal_pressed():
                print("down")
                device.emit(uinput.KEY_DOWN, 1)
            wheel_angle = wheel.get_angle()
            print(wheel_angle)
            if wheel_angle is not None:
                if wheel_angle > 10:
                    print("right")
                    device.emit(uinput.KEY_RIGHT, 1)
                elif wheel_angle < -10:
                    print("left")
                    device.emit(uinput.KEY_LEFT, 1)
            time.sleep(0.2)


if __name__ == "__main__":
    main()