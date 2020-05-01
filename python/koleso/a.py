"""
A simple Python script to send messages to a sever over Bluetooth
using PyBluez (with Python 2).
"""

import bluetooth


#nearby_devices = bluetooth.discover_devices(flush_cache=True,lookup_names=True)
#print (nearby_devices)

def find_device():
    nearby_devices = bluetooth.discover_devices()
    #Run through all the devices found and list their name
    num = 0
    print ("Select your device by entering its coresponding number...")
    for i in nearby_devices:
       num += 1
       print (str(num) + ": " , bluetooth.lookup_name( i ))

    selection = int(input("> ")) - 1
    print ("You have selected " + bluetooth.lookup_name(nearby_devices[selection]))
    bd_addr = nearby_devices[selection]
    return bd_addr


serverMACAddress = '20:16:05:23:17:28' # id not mac address, but some id
#serverMACAddress = print (bd_addr)

port = 1
s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

s.connect((serverMACAddress, port))
command = ''
while 1:
    command += s.recv(1024).decode('ascii').strip("'")
    if command.endswith('\n'):
        command  = command.strip()
        print (command)
        command =  ''

sock.close()
