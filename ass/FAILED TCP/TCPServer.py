from socket import *
from select import *
from utility import authenticate
import time
import datetime as dt
import sys

# python3 TCPServer.py server_port block_duration timeout
server_host = 'localhost'
server_port = int(sys.argv[1])
block_duration = int(sys.argv[2])
timeout = int(sys.argv[3])
# dict of client
clients = {}

server_socket = socket(AF_INET, SOCK_STREAM)

server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

server_socket.bind((server_host, server_port))

sockets_list = [server_socket]

# This makes server listen to new connections
server_socket.listen()

print(f'Server on {server_host}:{server_port}')

def recv_handler(connection_socket):
	try :

		message = connection_socket.recv(1024)

		return message.decode()
	except:
		return False

while (1):
	readable, writeable, exceptional = select(sockets_list, [], sockets_list)

	current_time = dt.datetime.now()
	date_time = current_time.strftime("%d/%m/%Y, %H:%M:%S")

	for notified_socket in readable:
		if notified_socket == server_socket:
			connection_socket, addr = server_socket.accept()

			credentials = recv_handler(connection_socket)

			print(credentials)

			if credentials == False:
				print('RIP')

			result = authenticate(credentials.split())

			if result == 'Login Successful':
				sockets_list.append(connection_socket)
				clients[connection_socket] = credentials.split()[0]

				print(f'New connection from {addr}, Username: {clients[connection_socket]} at {date_time}')
		
			connection_socket.send(result.encode())

		else:

			message = recv_handler(notified_socket)

			client = clients[notified_socket]

			print(f'Reveived message from {client}: {message} at {date_time}')
	
	print("-- loop end --")