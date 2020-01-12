import socket
import bluetooth
from threading import Thread
import logging

serverMACAddress = '20:16:05:23:17:28'
PORT = 1
LAST_SWITCH = 3

class TBluetoohKolesoThread(Thread):
    def __init__(self, switch_song_action):
        Thread.__init__(self)
        self.killed = False
        self.socket = None
        self.connect_bluetooth()
        self.current_switch = None
        self.switch_song_action = switch_song_action

    def connect_bluetooth(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((serverMACAddress, PORT))

    def IsForward (self, newSwitch):
        if self.current_switch == None:
            return True
        return newSwitch > self.current_switch  or (newSwitch == 0  and self.current_switch == LAST_SWITCH)


    def run(self):
        command = ''
        self.socket.settimeout(1)
        while not self.killed:
            try:
                command += self.socket.recv(1024).decode('ascii').strip("'")
                if command.endswith('\n'):
                    logging.debug ("command=" + command)
                    command  = command.strip()
                    newSwitch = int(command[len('switch'):])
                    logging.debug ("newSwitch=" + str(newSwitch))
                    is_forward = self.IsForward(newSwitch)
                    self.current_switch = newSwitch
                    self.switch_song_action(is_forward)
                    command = ''
            except OSError as e:
                pass # timeout
            except ValueError:
                logging.debug ("unparsable command  from arduino: {}".format(command))
