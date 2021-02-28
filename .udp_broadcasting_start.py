# udp start broadcasting
import socket
import time

msg0 = "TD-1,10-7b-44-87-76-51,1234567"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

while True:
    #msg = f"[{i}]{msg0}"    #ERORR=TypeError: a bytes-like object is required, not 'str'
    msg = f"{msg0}".encode("utf-8")
    sock.sendto(msg, ('192.168.43.255', 12345))
    print(msg)
    time.sleep(1)