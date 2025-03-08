from utils.racing_wheel import TRacingWheel
import time
from utils.logging_wrapper import setup_logging
from utils.uinput_wrapper import KeyControls



def main():
    logger = setup_logging("test_wheel")
    wheel = TRacingWheel(logger, -30, sound_pedals=False)
    keyboard = KeyControls()
    while True:
        wheel.read_wheel_events()
        if wheel.right_under_wheel_button in wheel.pressed_buttons:
            wheel.forget_key(wheel.right_under_wheel_button)
            print("center wheel")
            wheel.save_wheel_center()

        elif wheel.right_button in wheel.pressed_buttons:
            wheel.forget_key(wheel.right_button)
            keyboard.press_tab()
        elif wheel.left_button in wheel.pressed_buttons:
            wheel.forget_key(wheel.left_button)
            keyboard.click_left()

        if wheel.is_right_pedal_pressed():
            keyboard.press_up()
        elif wheel.is_left_pedal_pressed():
            keyboard.press_down()
        else:
            keyboard.unpress_up_and_down()

        wheel.read_wheel_events()
        wheel_angle = wheel.get_wheel_angle()

        if wheel_angle is not None:
            if wheel_angle > 10:
                keyboard.press_right()
            elif wheel_angle < -10:
                keyboard.press_left()
            else:
                keyboard.unpress_left_and_right()
        time.sleep(0.2)
        if keyboard.pressed_keys:
            print("are pressed {}".format(keyboard.pressed_keys))

if __name__ == "__main__":
    main()