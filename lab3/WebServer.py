# socket module, since can't use http.server module
# referenced from the examples given in webcms3
# got help from stackoverflow on the bug where browser 
# not displaying anything even after the file content is printed

from socket import *
import sys

if not (len(sys.argv) < 3 and len(sys.argv) > 1):
	print("Insufficent args -> python3 WebServer.py port")
	sys.exit()
else:
	serverPort = int(sys.argv[1])
	if serverPort == 80 or serverPort == 8080 or serverPort < 1024:
		print("use a non-standard port no.")
		sys.exit()

serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.bind(('localhost', serverPort))

serverSocket.listen(1)

print("Server is ready to receive!")

print("Running on http://127.0.0.1:" + str(serverPort) + "/")

while 1:
	connectionSocket, addr = serverSocket.accept()

	sentence = connectionSocket.recv(1024)
	# print("\n" + sentence.decode())

	fileName = sentence.split()[1][1:]
	# print("\n" + fileName.decode())

	try:	
		file = open(fileName, "r")
		response = file.read()
		file.close()

		# print("\n" + response)

		data = "HTTP/1.1 200 OK \r\n".encode()

		connectionSocket.send(data)
		# apparently my bug was \r\n at the content type need to be \r\n\r\n
		if "png".encode() in fileName:
			data = "Content-Type: image/png \r\n\r\n".encode()
			connectionSocket.send(data)
			# connectionSocket.send(response)
		if "html".encode() in fileName:
			data = "Content-Type: text/html \r\n\r\n".encode()
			connectionSocket.send(data)
			# connectionSocket.send(response)
		connectionSocket.send(response)
		connectionSocket.close()

		# for clarity on console if browser not showing
		print(fileName + " received!")

	except IOError:
		# for clarity on console if browser not showing
		print("404 File Not Found")

		data = "HTTP/1.1 404 File Not Found \r\n".encode()
		connectionSocket.send(data)
		data = "Content-Type: text/html \r\n\r\n".encode()
		connectionSocket.send(data)
		connectionSocket.send("<html><h1>404 File Not Found</h1><p>Try index.html or myimage.png !</p></html>".encode())
		connectionSocket.close()
