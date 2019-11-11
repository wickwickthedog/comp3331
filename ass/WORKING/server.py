'''
Used the sample code as the base from 
https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
Coding: utf-8
Editted by: z5147986
Usage: 
(easy) - python3 server.py
(default) - pyhton3 server.py <port> <block duration> <timeout>
'''
from socket import *
from select import *
from utility import authenticate
import sys
import datetime 

# for easy testing uncomment this
server_host = 'localhost'
server_port = 12000
block_duration = 60
timeout = 8

# FIXME
# for easy testing comment this
# server_port = int(sys.argv[1])
# block_duration = int(sys.argv[2])
# timeout = int(sys.argv[3])

# Create a socket
# socket.AF_INET - address family, server_hostv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw server_host packets
server_socket = socket(AF_INET, SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given server_host and server_port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface server_host
server_socket.bind((server_host, server_port))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and credentials as data
clients = {}

print(f'Listening for connections on {server_host}:{server_port}')

# Handles message receiving
def receive_message(client_socket):
    try:
        # Receive header containing message length, it's size is defined as 20
        message_header = client_socket.recv(20)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        # if not len(message_header):
        #     return False

        # Convert header to int value
        message_length = int(message_header.decode())

        # Return a dict object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:
        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

while (1):

    # Calls Unix select() system call or Windows select() WinSock call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
    #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    # Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send thru them
    #   - errors  - sockets with some exceptions
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select(sockets_list, [], sockets_list)

    # if not (read_sockets or exception_sockets):
    #     current_time = datetime.datetime.now()

    #     print("timeout: " + current_time.strftime("%H:%M:%S") + f' {read_sockets}')

    # Iterate over notified sockets
    for notified_socket in read_sockets:
        # user = clients[notified_socket]
        # if clients != None:
            # print(clients[notified_socket])

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            # Accept new connection
            client_socket, client_address = server_socket.accept()

            # DONE - LOGIN
            # Client send credentials
            while(1):
                user = receive_message(client_socket)
                # print("HI")
                # If False client disconnected before sending credentials
                if user is False:
                    continue

                # print(user['data'].decode()) # username,password
                credentials = user['data'].decode().split(',')
                # print(credentials[0]) # username
                # print(credentials[1]) # password    

                result = authenticate(credentials)
                print("AUNTHENTICATION: " + result)
                if 'Successful' in result:
                    # Add accepted socket to select() list
                    sockets_list.append(client_socket)
                    # for timeout
                    user['last-active'] = datetime.datetime.now()
                    # user will have user_header and credentials
                    clients[client_socket] = user

                    username = user['data'].decode().split(',')[0]
                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, username))
                    # client_socket.send(f'Welcome {username}'.encode())
                    message = f'Welcome back {username}!'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                    # message = f'Timeout if inactive,{timeout},Block Duration,{block_duration}'.encode()
                    # message_header = f"{len(message):<{20}}".encode()
                    # client_socket.send(message_header + message)
                    break;
                else:
                    message = result.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                    # message = f'Block Duration,{block_duration}'.encode()
                    # message_header = f"{len(message):<{20}}".encode()
                    # client_socket.send(message_header + message)

        # Else existing socket is sending a message
        else:
            # Receive message
            message = receive_message(notified_socket)

            current_time = datetime.datetime.now()
            print('{} - {}'.format(current_time, clients[notified_socket]['last-active']))
            minus_timeout = current_time - datetime.timedelta(seconds=timeout)
            if minus_timeout == clients[notified_socket]['last-active'] or minus_timeout > clients[notified_socket]['last-active']:
                print('Connection timeout for: {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                # send indication of termination to client
                notified_socket.shutdown(SHUT_RDWR)

                continue

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            user['last-active'] = datetime.datetime.now()

            print('Received message at {} from {}: {}'.format(user['last-active'], user["data"].decode().split(',')[0], message["data"].decode()))

            # Iterate over connected clients and broadcast message
            # for client_socket in clients:

                # But don't sent it to sender
                # if client_socket != notified_socket:

                    # Send user and message (both with their headers)
                    # We are reusing here message header sent by sender, and saved username header send by user when he connected
                    # client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
        # user = clients[notified_socket]
        # print('{}\'s last active: {}'.format(user['data'].decode().split(',')[0], user['last-active']))
        # notified_socket.settimeout(timeout)
        # print(notified_socket.gettimeout())

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]