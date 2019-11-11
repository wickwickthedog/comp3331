from socket import *
from select import *
import sys
import errno

# python3 TCPClient.py server_port block_duration timeout
server_name = sys.argv[1]
server_port = int(sys.argv[2])

client_socket = socket(AF_INET, SOCK_STREAM)

client_socket.connect((server_name, server_port))

client_socket.setblocking(False)

username = input("ENTER USERNAME: ")
password = input("ENTER PASSWORD: ")

while (1):
	credentials = username.replace(' ', ' ') + ' ' + password.replace(' ', ' ')

	# print(credentials)
	try:
		client_socket.send(credentials.encode())

		while (1):

			message = client_socket.recv(1024)
			print(message.decode())

			if 'Username' in message.decode(): # == 'Invalid Username. Please try again!':
				username = input("ENTER USERNAME: ")
				password = input("ENTER PASSWORD: ")
				continue
			elif 'Password' in message.decode(): # == 'Invalid Password. Please try again!':
				password = input("ENTER PASSWORD: ")
				continue
			else:
				command = input("> ")
	except IOError as e:
		if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
			print('Reading error: {}'.format(str(e)))
			sys.exit()
		continue
	except Exception as e:
		print('Reading error: {}'.format(str(e)))
		sys.exit()

