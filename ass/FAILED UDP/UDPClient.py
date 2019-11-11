#Python 3
#Usage: python3 UDPClient3.py localhost 12000
#coding: utf-8
from socket import *
from utility import authenticate
import sys

#Server would be running on the same host as Client
# TODO change it to sys.argv[1]
# serverName = sys.agrv[1]
serverName = "127.0.0.1"
# TODO change it to sys.argv[2]
# serverPort = int(sys.argv[2])
serverPort = 12000
# TODO block
retryCount = 1

clientSocket = socket(AF_INET, SOCK_DGRAM)

username = input("ENTER USERNAME: ")
password = input("ENTER PASSWORD: ")

credentials = username.replace(' ', ' ') + ' ' + password.replace(' ', ' ')

while (1):
	# message = input("Please type Subscribe\n")
	

	message = authenticate(credentials.split())
	#print("-- RESULT -- " + message)

	clientSocket.sendto(message.encode(),(serverName, serverPort))
	#wait for the reply from the server
	receivedMessage, serverAddress = clientSocket.recvfrom(2048)

	if (receivedMessage.decode() =='Login Successful'):
		print("Welcome to WICKWICK's console chat service!")
		#Wait for 10 back to back messages from server
		while (1):
		# for i in range(10):
			receivedMessage, serverAddress = clientSocket.recvfrom(2048)
			print(receivedMessage.decode())
	elif (receivedMessage.decode() == 'Invalid Password'):
		print("Invalid Password. Please try again - " + str(retryCount))
		if retryCount >= 3:
			print(username + ", you are blocked!")
			
		retryCount += 1
		password = input("ENTER PASSWORD: ")
		credentials = username.replace(' ', ' ') + ' ' + password.replace(' ', ' ')

#prepare to exit. Send Unsubscribe message to server
message='Unsubscribe'
clientSocket.sendto(message.encode(),(serverName, serverPort))
clientSocket.close()
# Close the socket