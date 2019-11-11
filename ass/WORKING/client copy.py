'''
Used the sample code as the base from 
https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/?completed=/server-chatroom-sockets-tutorial-python-3/
Coding: utf-8, Python 3
Editted by: z5147986
Usage: 
(easy) - python3 client.py
(default) - pyhton3 client.py <host> <port>
'''
from socket import *
import errno
import sys

# for easy testing uncomment this
server_name = 'localhost'
server_port = 12000

# FIXME
# for easy testing comment this
# server_name = sys.argv[1]
# server_port = int(sys.argv[2])

# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw server_name packets
client_socket = socket(AF_INET, SOCK_STREAM)

# Connect to a given server_name and server_port
client_socket.connect((server_name, server_port))

# Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
client_socket.setblocking(False)

# Prepare username and header and send them
# We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
username = input("Username: ")
username = username.encode()
user_header = f"{len(username):<{20}}".encode()
# print(user_header+username)
client_socket.send(user_header + username)

while True:
    print(f'{username.decode()}\'s console')
    # Wait for user to input a message
    message = input(f'{username.decode()} > ')

    # If message is not empty - send it
    if message:

        # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
        message = message.encode()
        message_header = f"{len(message):<{20}}".encode()
        client_socket.send(message_header + message)

    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        while True:

            # Receive our "header" containing username length, it's size is defined and constant
            user_header = client_socket.recv(20)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(user_header):
                print('Connection closed by the server')
                sys.exit()

            # Convert header to int value
            username_length = int(user_header.decode())

            # Receive and decode username
            username = client_socket.recv(username_length).decode()

            # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
            message_header = client_socket.recv(20)
            message_length = int(message_header.decode())
            message = client_socket.recv(message_length).decode()

            # Print message
            print(f'{username} > {message}')

    except IOError as e:
        # This is normal on non blocking connections - when there are no incoming data error is going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
        # If we got different error code - something happened
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        print('Reading error: '.format(str(e)))
        sys.exit()