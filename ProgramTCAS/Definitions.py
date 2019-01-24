from threading import Lock as Mutex


class Global:
	SAMPLING_FREQ = 15
	SAMPLING_TIME = 1/SAMPLING_FREQ
	MY_PORT = "8000"
	MUTEX_CONN = Mutex()
	FINISH = False


def is_on(str):
	while True:
		answer = input("You wish to connect to " + str + " systems?[y/n]   ")
		if answer == "y":
			return True
		elif answer == "n":
			return False
		else:
			print("Unvalid answer. Please, answer 'y' or 'n'.")

def how_many(str):
	while True:
		try:
			answer = input("How many " + str + " systems?   ")
			N = int(answer)
			if str == "TCAS" and N>=0:
				return N
			elif str == "emulator" and N>0:
				return N
			else:
				print("Not a valid number... Try again.")
		except:
			print("Not a valid number... Try again.")

def ip(whos):
	while True:
		try:
			ip = input("Insert " + whos + " ip:  ")
			return ip
		except:
			print("Invalid input. Please try again.")

def port(whos):
	while True:
		try:
			port = int(input("Insert " + whos + " port:   "))
			return port
		except:
			print("Invalid port. Please try again.")
