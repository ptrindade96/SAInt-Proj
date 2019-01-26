import socket
import struct
from threading import Thread
from threading import Lock as Mutex
from Definitions import Global


class XPlaneConnection:

    IP = '127.0.0.1'
    TIMEOUT = None

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thread_recv = Thread(target=self.__rcv_thread__)
        self.mutex_values = Mutex()
        self.values = self.__init_values__()
        self.OK = False
        return

    def connect(self, port_):
        try:
            self.port = port_
            self.sock.bind((XPlaneConnection.IP, self.port))
            self.OK = True
            self.thread_recv.start()
            return True
        except:
            return False

    def is_on(self):
        return self.OK

    def get_values(self):
        self.mutex_values.acquire()
        return_values = self.values.copy()
        self.mutex_values.release()
        return return_values

    def stop_simulation(self):
        self.OK = False
        return

    def __rcv_thread__(self):
        self.sock.settimeout(XPlaneConnection.TIMEOUT)
        while self.OK and not Global.FINISH:
            try:
                data = self.sock.recv(1024)
                self.mutex_values.acquire()
                self.__decode_data__(data)
                self.mutex_values.release()
            except:
                self.OK = False
                self.sock.close()
                return
        self.OK = False

    def __decode_data__(self, data):
        i = 0
        while 5 + (i+1)*36 <= len(data):
            d = struct.unpack('i8f', data[5 + i * 36:5 + (i + 1) * 36])
            if d[0] == 20:
                self.values['lat'] = d[1]
                self.values['lon'] = d[2]
                self.values['alt'] = d[3]
            elif d[0] == 19:
                self.values['hpath'] = d[3]
                self.values['vpath'] = d[4]
            elif d[0] == 3:
                self.values['IAS_knots'] = d[1]
                self.values['EAS_knots'] = d[2]
                self.values['TAS_knots'] = d[3]
                self.values['GS_knots'] = d[4]
            elif d[0] == 104:
                self.values['ILS_OM'] = d[1]
                self.values['ILS_MM'] = d[2]
                self.values['ILS_IM'] = d[3]
            i += 1
        return

    @staticmethod
    def __init_values__():
        values = dict()
        values["lat"] = 38.79
        values["lon"] = -9.14
        values["alt"] = 0
        values["vpath"] = 0
        values["hpath"] = 0
        values["GS_knots"] = 0
        values["IAS_knots"] = 0
        values["EAS_knots"] = 0
        values["TAS_knots"] = 0
        values["ILS_OM"] = 0
        values["ILS_MM"] = 0
        values["ILS_IM"] = 0
        return values
