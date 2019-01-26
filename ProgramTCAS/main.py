import sys
import time
import numpy
import threading
import Definitions as Prompt
from Definitions import Global
from Connections import TcasConnection
from Connections import EmulatorConnection
from Connections import Acceptor
from XPlane import XPlaneConnection
import TCAS


################################################################################
##								Main function 								  ##
################################################################################
if __name__ == '__main__':
	print("\n------------------------------------------------------")
	print("__________________ Starting Program __________________")
	print("------------------------------------------------------")

	# Begin connection with XPlane
	Simul = XPlaneConnection()
	XPlane_port = Prompt.port("XPlane")
	while not Simul.connect(XPlane_port):
		print("XPlane connection failed.")
		answer = input("Try again?[y/n]  ")
		if answer == 'n':
			sys.exit(5)
		elif answer == 'y':
			XPlane_port = Prompt.port("XPlane")

	EMUL_ON = Prompt.is_on("emulator")
	if EMUL_ON:
		n = Prompt.how_many("emulator")
		emulator_connections = []
		i = 1
		while n > 0:
			ip = Prompt.ip("emulator " + repr(i))
			port = Prompt.port("emulator " + repr(i))
			C = EmulatorConnection(ip,port)
			emulator_connections.append(C)
			n = n - 1
			i = i + 1

	TCAS_ON = Prompt.is_on("TCAS")
	if TCAS_ON:
		n = Prompt.how_many("TCAS")
		tcas_connections = []
		i = 1
		while n > 0:
			ip = Prompt.ip("TCAS number "+repr(i))
			port = Prompt.port("TCAS number "+repr(i))
			C = TcasConnection(ip, port)
			if C.connect():
				C.start_rcv()
				tcas_connections.append(C)
				n = n - 1
				i = i + 1
			else:
				print("Unable to connect to endpoint. Try inserting again.")
		Tcas = TCAS.TCAS()
		Global.MUTEX_CONN.acquire()
		for connection in tcas_connections:
			Tcas.new_airplane(connection.id,connection.get_values())
		Global.MUTEX_CONN.release()
		A = Acceptor(tcas_connections, Global.MY_PORT, Tcas)
		A.start_accept()
		print("Started accepting connections on port " + repr(Global.MY_PORT))

	if not TCAS_ON and not EMUL_ON:
		print("So... you wish to do nothing...")
		print("Then I will exit...")
		Simul.stop_simulation()
		sys.exit(0)

	while Simul.is_on():
		my_values = Simul.get_values()
		others_values = []
		if TCAS_ON:
			Global.MUTEX_CONN.acquire()
			for connection in tcas_connections:
				connection_values = connection.get_values()
				connection_values['id'] = connection.id
				others_values.append(connection_values)
				if not connection.send(my_values):  # connection died..
					tcas_connections.remove(connection)
			Tcas.update(my_values, others_values)
			Global.MUTEX_CONN.release()
			Tcas.clock.tick(TCAS.SAMPLING_TIME)
			if Tcas.exited():
				Tcas.quit()
				TCAS_ON = False
		if EMUL_ON:
			for connection in emulator_connections:
				connection.send(my_values)
		time.sleep(Global.SAMPLING_TIME)


	print("Not receiving from XPlane")
	Global.FINISH = True
	if TCAS_ON:
		Tcas.quit()
		A.stop_accept()
		tcas_connections = []
	print("Exiting.")
	sys.exit(0)
