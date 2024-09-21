import time


import uinput

def main():
    print ("press_a_key")
    # with uinput.UInput() as ui:
    #     ui.write(ecodes.EV_KEY, ecodes.KEY_A, 1)
    #     time.sleep(0.05)
    #     ui.write(ecodes.EV_KEY, ecodes.KEY_A, 0)
    #     ui.syn()
    time.sleep(1)
    with uinput.Device([uinput.KEY_W]) as device:
        for i in range (10):
            device.emit(uinput.KEY_W, 1)
            time.sleep(1)
            device.emit(uinput.KEY_W, 0)


if __name__ == "__main__":
    main()