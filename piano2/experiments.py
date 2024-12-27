# if __name__ == '__main__':
#     pa_list_devices()
#     s = Server(audio="alsa")
#     s.setInOutDevice(6)
#     s.setMidiInputDevice(6)
#     s.boot()
#     s.start()
#     #a = Sine(mul=0.01).out(dur=2.0)
#     #time.sleep(2)
#
#     notes = Notein(poly=10, scale=1, mul=.5)
#     bend = Bendin(brange=2, scale=1)
#     p = Port(notes['velocity'], .001, .5)
#     b = Sine(freq=notes['pitch'] * bend, mul=p).out()
#     c = Sine(freq=notes['pitch'] * bend * 0.997, mul=p).out()
#     d = Sine(freq=notes['pitch'] * bend * 1.005, mul=p).out()
#
#     s.gui(locals())
#     s.stop()
#
#     #logger = setup_logging("piano2")
#     #main(logger)
#     #logger.info("exit from main")
#

from pythonosc import udp_client


if __name__ == "__main__":
  client = udp_client.SimpleUDPClient("127.0.0.1", 1337)
  #client.send_message("/last_xmz", "aaa")
    client.send_message("/Panic", "")
  #client.send_message("/Panic", "")
  #data = client._sock.recvfrom(1024)
  pass


# import socket
#
# if __name__ == "__main__":
#     osc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     server_address = ("127.0.0.1", 1337)
#     #osc_socket.bind(server_address)
#
#     #while True:
#     osc_socket.sendto(b'/Panic\x00\x00,s\x00\x00\x00\x00\x00\x00', server_address)
#     #osc_socket.sendto(b"/part0/ctl/volume.receive", server_address)
#     print("####### Server is listening #######")
#     data, address = osc_socket.recvfrom(4096)
#     print("\n\n 2. Server received: ", data.decode('utf-8'), "\n\n")

# import pyliblo3
# if __name__ == "__main__":
#     osc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
