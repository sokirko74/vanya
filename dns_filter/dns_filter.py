#!/usr/bin/env python3

#1. sudo pip install dnslib
#2
#sudo nmcli connection show
#sudo nmcli connection modify "RossiaBezPutina" ipv4.dns "127.0.0.59"
#sudo nmcli connection modify "RossiaBezPutina" ipv4.ignore-auto-dns yes
#sudo nmcli connection modify "RossiaBezPutina" ipv6.ignore-auto-dns yes
#sudo nmcli connection down RossiaBezPutina; sudo nmcli connection up RossiaBezPutina;

#3. sudo nano /etc/systemd/system/dns_filter.service
# [Unit]
# Description=DnsFilter
# After=network.target
# [Service]
# ExecStart=/usr/bin/python3 /home/sokirko/dns_filter.py
# WorkingDirectory=/home/sokirko
# User=root
# Restart=always
# RestartSec=5
# Environment=PYTHONUNBUFFERED=1
#
# [Install]
# WantedBy=multi-user.target


import socket
import threading
import re
from dnslib import DNSRecord, DNSHeader, RCODE

BLACK_DOMAINS={
    "www.google.com",
    "google.com",
    "ya.ru",
    "yandex.ru",
    "youtube.com",
    "www.youtube.com",
    "youtube-ui.l.google.com",
    "wide-youtube.l.google.com"
}

yandex = ["yandex.ru","ya.ru","bookmate.ru", "bookmate.yandex.net", "yastatic.net"]
google = ["gmail.com",
          "googleapis.com", "gstatic.com",
          "google.com"
          ]
wb = ["wb.ru", "wbbasket.ru", "wildberries.ru"]
whatsup = ["whatsapp.com", "whatsapp.net"]
wiki = ["wikipedia.org", "wikimedia.org"]
mosru = ["mos.ru", "wikimedia.org"]
system = ["ubuntu.com"]
white = yandex + google + wb + whatsup + wiki + mosru + system
white_re_str = "|".join(map(lambda x: "({}$)".format(x), white))
WHITE_REGEXP = re.compile(white_re_str)

def check_domain(qname):
    qname = qname.rstrip(".")
    res =  WHITE_REGEXP.search(qname) and qname not in BLACK_DOMAINS
    return res
assert check_domain("mail.yandex.ru.")
assert not check_domain("yandex.ru.")
assert check_domain("mos.ru")

UPSTREAM_DNS = ("8.8.8.8", 53)
LISTEN_ADDR = "127.0.0.59"
LISTEN_PORT = 53




def handle_request(data, addr, sock):
    try:
        request = DNSRecord.parse(data)
        qname = str(request.q.qname)
        print(f"Запрос от {addr}: {qname}")

        if not check_domain(qname):
            print(f"Блокируем: {qname}")
            reply = DNSRecord(
                DNSHeader(id=request.header.id, qr=1, aa=1, ra=1, rcode=RCODE.NXDOMAIN),
                q=request.q
            )
            sock.sendto(reply.pack(), addr)
        else:
            print(f"Проксируем: {qname}")
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_sock:
                upstream_sock.settimeout(5)
                upstream_sock.sendto(data, UPSTREAM_DNS)
                response, _ = upstream_sock.recvfrom(4096)
                sock.sendto(response, addr)
    except Exception as e:
        print(f"Ошибка: {e}")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_ADDR, LISTEN_PORT))
    print(f"DNS-прокси запущен на {LISTEN_ADDR}:{LISTEN_PORT}")

    while True:
        data, addr = sock.recvfrom(512)
        threading.Thread(target=handle_request, args=(data, addr, sock)).start()

if __name__ == "__main__":
    main()
