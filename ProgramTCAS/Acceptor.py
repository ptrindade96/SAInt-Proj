import socket
import threading
from Connections import TcasConnection
from Definitions import Global

# Include connection sinc here


class Acceptor:

    def __init__(self, connections, port_,Tcas_):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.threadAcceptor = threading.Thread(target=self.__acceptor__)
        self.connections = connections
        self.port = int(port_)
        self.Tcas = Tcas_
        return

    def __del__(self):
        self.sock.close()
        return

    def __acceptor__(self):
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen(1)
        while True:
            try:
                sock, addr = self.sock.accept()
                conn = TcasConnection('0.0.0.0', self.port, sock)
                conn.start_rcv()
                Global.MUTEX_CONN.acquire()
                self.Tcas.new_airplane(conn.id,conn.get_values())
                self.connections.append(conn)
                Global.MUTEX_CONN.release()
            except:
                print("Accept error.")
                self.sock.close()
                return

    def start_accept(self):
        self.threadAcceptor.start()
        return
