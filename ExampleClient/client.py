import socket
import struct

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 10000))
if True:
    buff, addr = sock.recvfrom(1024)
    
