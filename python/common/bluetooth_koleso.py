import socket
import bluetooth
from threading import Thread
import logging

serverMACAddress = '20:16:05:23:17:28'
PORT = 1
FIRST_SWITCH = 0
LAST_SWITCH = 3


def is_forward_movement(old_switch, new_switch):
    if old_switch is None:
        return True
    if old_switch == LAST_SWITCH and new_switch == FIRST_SWITCH:
        return True
    if old_switch == FIRST_SWITCH and new_switch == LAST_SWITCH:
        return False
    return old_switch < new_switch


class TBluetoohKolesoThread(Thread):
    def __init__(self, logger, switch_song_action):
        Thread.__init__(self)
        self.killed = False
        self.socket = None
        self.connect_bluetooth()
        self.current_switch = None
        self.switch_song_action = switch_song_action
        self.logger = logger

    def connect_bluetooth(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((serverMACAddress, PORT))

    def run(self):
        commands = ''
        self.socket.settimeout(1)
        while not self.killed:
            try:
                data = self.socket.recv(1024).decode('ascii')
                commands += data.strip("'")
                if commands.endswith('\n'):
                    logging.debug ("commands=" + commands.strip())
                    for command in commands.split("\n"):
                        command  = command.strip()
                        if len(command) == 0:
                            continue
                        new_switch = int(command[len('switch'):])
                        is_forward = is_forward_movement(self.current_switch, new_switch)
                        self.current_switch = new_switch
                        self.switch_song_action("up" if is_forward else "down")
                    commands = ''
            except OSError as e:
                pass # timeout
            except ValueError:
                self.logger.debug("unparsable command  from arduino: {}".format(commands))
                commands = ''
        self.logger.debug("exit from TBluetoohKolesoThread")
        self.socket.close()