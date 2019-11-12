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
timeout = 1200

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

# list of blocked clients
blocked_clients = {}

# list of logged out clients
logged_out_clients = {}

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

    # --- timeout start ---
    for timeout_socket in list(clients):
        current_time = datetime.datetime.now()
        if 'last-active' in clients[timeout_socket]:
            print('{} - {}'.format(current_time, clients[timeout_socket]['last-active']))
            minus_timeout = current_time - datetime.timedelta(seconds=timeout)
            if minus_timeout == clients[timeout_socket]['last-active'] or minus_timeout > clients[timeout_socket]['last-active']:
                print('Connection timeout for: {}'.format(clients[timeout_socket]['data'].decode().split(',')[0]))
                # message = '{} timeout due to inactivity...'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                # message_header = f"{len(message):<{20}}".encode()
                # client_socket.send(message_header + message)

                # add to logged out list
                logged_out_clients[notified_socket] = clients[notified_socket]

                # Remove from list for socket.socket()
                sockets_list.remove(timeout_socket)

                # Remove from our list of users
                del clients[timeout_socket]

                # send indication of termination to client
                timeout_socket.shutdown(SHUT_RDWR)
                timeout_socket.close()
    # --- timeout end ---

    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket and notified_socket not in clients:

            # Accept new connection
            client_socket, client_address = server_socket.accept()
            
            # to track retry count
            retry_count = 0

            # Client send message
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

                # check blocked account
                # --- block_duration start ---
                check = None
                for notified_socket in blocked_clients:
                    # print("TRUE")
                    # print(blocked_clients[notified_socket]['data'].decode())
                    # print(credentials[0])
                    # print(blocked_clients[notified_socket]['data'].decode())
                    if blocked_clients[notified_socket]['data'].decode() == clients[notified_socket]['data'].decode(): #'account-blocked' in blocked_clients[notified_socket]: # or clients[notified_socket]['data'].decode() == credentials[0]: 
                        # print(type(clients[notified_socket]))
                        # print("BLOCKED " + blocked_clients[notified_socket]['data'].decode())
                        # print("CLIENT " + clients[notified_socket]['data'].decode())
                        username = blocked_clients[notified_socket]['data'].decode() #.split(',')[0]
                        current_time = datetime.datetime.now()
                        minus_blocked = current_time - datetime.timedelta(seconds=block_duration)
                        # print('{} vs {}'.format(minus_blocked, clients[client_socket]['account-blocked']))
                        if minus_blocked > blocked_clients[notified_socket]['account-blocked']:
                            print(f'{username}\'s account has been UNBLOCKED!')
                            if username == credentials[0]:
                                message = f'Your account have been UNBLOCKED, {username}!'.encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)
                                sockets_list.remove(notified_socket)
                                del blocked_clients[notified_socket]
                                del clients[notified_socket]
                                check = 'unblocked'
                            break
                        # else:
                        elif minus_blocked < blocked_clients[notified_socket]['account-blocked'] or minus_blocked == blocked_clients[notified_socket]['account-blocked']:
                            print(f'{username} is still BLOCKED!')
                            check = username
                            # counter = 1
                            if username == credentials[0]:
                                message = 'Your account is blocked {}. Please try again after {}!'.format(username, (blocked_clients[notified_socket]['account-blocked'] + datetime.timedelta(seconds=block_duration)).strftime("%d/%m/%Y, %H:%M:%S")).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)
                            break
                    continue

                if check == credentials[0]:
                    message = f'Your account is blocked {credentials[0]}!'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                    break
                # --- block_duration end ---

                # --- Authentication start ---
                result = authenticate(credentials)

                print(f'AUTHENTICATION for {credentials[0]}: {result}')
                if 'Successful' in result:
                    # remove from logged out list
                    for logged_out_socket in logged_out_clients:
                        if logged_out_clients[logged_out_socket]['data'].decode().split(',')[0] == credentials[0]:
                            del logged_out_clients[logged_out_socket]
                            break

                    # Add accepted socket to select() list
                    sockets_list.append(client_socket)

                    # to check user inactivity - timeout
                    user['last-active'] = datetime.datetime.now()
                    # user will have user_header and credentials
                    clients[client_socket] = user

                    username = user['data'].decode().split(',')[0]
                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, username))
                    # client_socket.send(f'Welcome {username}'.encode())

                    message = '--------------------'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = 'supported commands:'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = 'broadcast <msg>'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = 'whoelse'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = 'whoelsesince <time>'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = '--------------------'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = f'Welcome back {username}!'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                    break
                else:
                    if 'Password' in result:
                        retry_count += 1
                        user['retry'] = retry_count
                        # print(user['retry'])
                        if user['retry'] >= 3:
                            print(f'{credentials[0]}\'s account is BLOCKED')
                            user['account-blocked'] = datetime.datetime.now()
                            message = 'Invalid Password. Please try again later after {}. {}, Your account has been blocked!'.format((user['account-blocked'] + datetime.timedelta(seconds=block_duration)).strftime("%d/%m/%Y, %H:%M:%S"), credentials[0]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            client_socket.send(message_header + message)
                            
                            user['data'] = credentials[0].encode()
                            # Add accepted socket to select() list
                            sockets_list.append(client_socket)
                            # user will have user_header and block duration
                            blocked_clients[client_socket] = user
                            clients[client_socket] = user
                            break
                            # client_socket.setblocking(True)
                            # client_socket.shutdown(SHUT_RDWR)
                        else:
                            result = result + ' retry count: {}'.format(user['retry'])
                            message = result.encode()
                            message_header = f"{len(message):<{20}}".encode()
                            client_socket.send(message_header + message)
                    else:
                        message = result.encode()
                        message_header = f"{len(message):<{20}}".encode()
                        client_socket.send(message_header + message)
                # --- Authentication end ---

        # Else existing socket is sending a message
        elif notified_socket in clients and notified_socket not in blocked_clients:
        # else:
            
            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))

                # FIXME add to logged out list
                if notified_socket not in logged_out_clients:
                    logged_out_clients[notified_socket] = clients[notified_socket]

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            user['last-active'] = datetime.datetime.now()

            print('Received message at {} from {}: {}'.format(user['last-active'], user["data"].decode().split(',')[0], message["data"].decode()))

            #TODO commands
            command = message["data"].decode().split(' ')[0]
            if command == 'broadcast':
                try:
                    message['data'] = message['data'].decode().split(' ', 1)[1].encode()
                    # Iterate over connected clients and broadcast message
                    for client_socket in clients:

                        # But don't sent it to sender
                        if client_socket != notified_socket:

                            # Send user and message (both with their headers)
                            # We are reusing here message header sent by sender, and saved username header send by user when he connected
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                except:
                    print('FAIL: No message to broadcast, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'No message to broadcast, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            elif command == 'whoelse':
                for client_socket in clients:
                    if client_socket != notified_socket and client_socket not in blocked_clients:
                        message = '{} is online!'.format(clients[client_socket]['data'].decode().split(',')[0]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
            elif command == 'whoelsesince':
                try:
                # message['data'] = message['data'].decode().split(' ', 1)[1]
                # if message['data'].decode().split(' ')[1]:
                    # print(message['data'].decode())
                    # currently logged in user
                    for client_socket in clients:
                    # if 'last-active' in clients[client_socket]:
                        current_time = datetime.datetime.now()
                        sec = message['data'].decode()
                        sec = int(sec.split(' ')[1])
                        # print(type(sec))
                        # print(message['data'].decode())
                        t = clients[client_socket]['last-active'] + datetime.timedelta(seconds=sec)
                        if client_socket != notified_socket and client_socket not in blocked_clients and client_socket not in logged_out_clients:
                            # print("Last active" + clients[client_socket]['last-active'].strftime("%H:%M:%S"))
                            # print("current time is " + current_time.strftime("%H:%M:%S"))
                            if t > current_time or t == current_time:
                                msg = '{} IS online, last active: {}!'.format(clients[client_socket]['data'].decode().split(',')[0], clients[client_socket]['last-active'].strftime("%H:%M:%S")).encode()
                                message_header = f"{len(msg):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + msg)
                    for client_socket in logged_out_clients:
                    # if 'last-active' in clients[client_socket]:
                        current_time = datetime.datetime.now()
                        sec = message['data'].decode()
                        sec = int(sec.split(' ')[1])
                        # print(type(sec))
                        # print(message['data'].decode())
                        t = logged_out_clients[client_socket]['last-active'] + datetime.timedelta(seconds=sec)
                        if client_socket != notified_socket and client_socket not in blocked_clients and client_socket not in clients:
                            # print("Last active" + clients[client_socket]['last-active'].strftime("%H:%M:%S"))
                            # print("current time is " + current_time.strftime("%H:%M:%S"))
                            if t > current_time or t == current_time:
                                msg = '{} WAS online, last active: {}!'.format(logged_out_clients[client_socket]['data'].decode().split(',')[0], logged_out_clients[client_socket]['last-active'].strftime("%H:%M:%S")).encode()
                                message_header = f"{len(msg):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + msg)

                except:
                # else:
                    print('FAIL: No time specified, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'No time specified, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                

            else:
                print('FAIL: Invalid Command, {}!'.format(clients[notified_socket]['data'].decode().split(',')[0]))
                message = 'Error, Invalid Command, {}!'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                message_header = f"{len(message):<{20}}".encode()
                notified_socket.send(user['header'] + user['data'] + message_header + message)
    
    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]