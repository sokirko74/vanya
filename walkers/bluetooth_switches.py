import bluetooth
from threading import Thread

PORT = 1


class TBluetoohSwitchesThread(Thread):
    def __init__(self, logger, mac_address, switch_song_action):
        Thread.__init__(self)
        self.killed = False
        self.socket = None
        self.mac_address = mac_address
        self.logger = logger
        self.current_switch = None
        self.switch_song_action = switch_song_action
        self.connect_bluetooth()

    def connect_bluetooth(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((self.mac_address, PORT))

    def run(self):
        commands = ''
        self.socket.settimeout(1)
        while not self.killed:
            try:
                data = self.socket.recv(1024).decode('ascii')
                commands += data.strip("'")
                if commands.endswith('\n'):
                    self.logger.debug ("commands=" + commands.strip())
                    for command in commands.split("\n"):
                        command  = command.strip()
                        if len(command) == 0:
                            continue
                        new_switch = int(command[len('switch'):])
                        is_forward = is_forward_movement(self.current_switch, new_switch)
                        self.current_switch = new_switch
                        self.switch_song_action(is_forward)
                    commands = ''
            except OSError as e:
                pass # timeout
            except ValueError:
                self.logger.debug ("unparsable command  from arduino: {}".format(commands))
                commands = ''
        self.socket.close()