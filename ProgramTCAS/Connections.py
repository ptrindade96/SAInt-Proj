import socket
import errno
import struct
from threading import Thread
from threading import Lock as Mutex
from Definitions import Global

# self.valid does not require mutex (atomic variable -> atomic operations)

class Acceptor:

    def __init__(self, connections, port_,Tcas_):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.threadAcceptor = Thread(target=self.__acceptor__)
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
        while not Global.FINISH:
            try:
                sock, addr = self.sock.accept()
                conn = TcasConnection('0.0.0.0', self.port, sock)
                conn.start_rcv()
                Global.MUTEX_CONN.acquire()
                self.Tcas.new_airplane(conn.id,conn.get_values())
                self.connections.append(conn)
                Global.MUTEX_CONN.release()
            except:
                if not Global.FINISH:
                    print("Accept error.")
                    Global.FINISH = True
                else:
                    try:
                        self.sock.close()
                    except:
                        pass
                    return

    def start_accept(self):
        self.threadAcceptor.start()
        return

    def stop_accept(self):
        try:
            self.sock.close()
        except:
            pass
        return

class TcasConnection:

    count = 100

    def __init__(self, ip_, port_, sock_=None):
        self.ip = ip_
        self.port = port_
        self.thread_rcv = Thread(target=self.__receive__)
        self.mutex_values = Mutex()
        if sock_== None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock_
        TcasConnection.count += 1
        self.id = TcasConnection.count
        self.values = self.__init_values__()
        self.valid = True
        return

    def __del__(self):
        self.sock.close()
        try:
            self.thread_rcv.join()
        except:
            pass
        return

    def connect(self):
        try:
            self.sock.connect((self.ip, self.port))
            return True
        except socket.error as e:
            print(e)
            self.valid = False
            return False

    def start_rcv(self):
        self.thread_rcv.start()
        return

    def get_values(self):
        self.mutex_values.acquire()
        return_values = self.values.copy()
        self.mutex_values.release()
        return return_values

    def __update_data__(self, data):
        list_ = struct.unpack("!5f", data)
        self.values["lat"] = list_[0]
        self.values["lon"] = list_[1]
        self.values["alt"] = list_[2]
        self.values["vpath"] = list_[3]
        self.values["GS_knots"] = list_[4]
        return

    def __receive__(self):
        while not Global.FINISH:
            if self.valid:
                try:
                    data = self.sock.recv(20)
                    self.mutex_values.acquire()
                    self.__update_data__(data)
                    self.mutex_values.release()
                except socket.error as e:
                    if e.errno == errno.ECONNRESET:
                        print("Client disconnected")
                        self.valid = False
                        return
                except:
                    pass
            else:
                return

    def send(self, data):
        if self.valid:
            try:
                a = data["lat"]
                b = data["lon"]
                c = data["alt"]
                d = data["vpath"]
                e = data["GS_knots"]
                buff = struct.pack("!5f", a, b, c, d, e)
                self.sock.send(buff)
            except socket.error as e:
                if e.errno == errno.ECONNRESET:
                    print("Client disconnected")
                    self.valid = False
        return self.valid

    @staticmethod
    def __init_values__():
        values = dict()
        values["lat"] = 0
        values["lon"] = 0
        values["alt"] = 0
        values["vpath"] = 0
        values["GS_knots"] = 0
        return values


class EmulatorConnection:

    def __init__(self,ip_,port_):
        self.ip = ip_
        self.port = port_
        self.emulator_addr = (self.ip,self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return

    def connect(self):
        try:
            self.sock.bind((self.IP, self.PORT))
            return True
        except socket.error as e:
            print(e)
            return False

    def send(self, values):
        try:
            string = str(values["lat"]) + ','
            string += str(values["lon"]) + ','
            string += str(values["alt"]) + ','
            string += str(values["vpath"]) + ','
            string += str(values["hpath"]) + ','
            string += str(values["GS_knots"]) + ','
            string += str(values["IAS_knots"]) + ','
            string += str(values["EAS_knots"]) + ','
            string += str(values["TAS_knots"]) + ','
            string += str(values["ILS_OM"]) + ','
            string += str(values["ILS_MM"]) + ','
            string += str(values["ILS_IM"])
            self.sock.sendto(string.encode('ascii'), self.emulator_addr)
            return True
        except socket.error as e:
            print(e)
            return False
