'''
Used the sample code as reference from 
https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
Coding: utf-8
Editted by: z5147986
Usage: 
(default) - pyhton3 server.py <port> <block duration> <timeout>
'''

from socket import *
from select import *
from utility import receive_message, authenticate, user_exists_On9clients
import sys
import time
import datetime

server_host = 'localhost'
server_port = 12000
block_duration = 60
timeout = 120

# FIXME before submitting
# server_host = 'localhost'
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
# ensures that socket resuse is setup BEFORE it is bound. Will avoid the TIME_WAIT issue
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given server_host and server_port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface server_host
server_socket.bind((server_host, server_port))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select()
sockets_list = [server_socket]

# List of connected clients: socket as key
online_clients = {}

# List of blocked clients socket as key
blocked_clients = {}

# List of disconnected clients: socket as key
offline_clients = {}

print(f'Listening for connections on {server_host}:{server_port}\n')

# while len(clients) < 2:
while (1):
    # read_sockets are sockets we received some data on
    read_sockets, _, _ = select(sockets_list, [], [], 1)

    for notified_socket in read_sockets:

        if notified_socket is server_socket:

            # Accept new connection
            client_socket, client_address = server_socket.accept()

            # to track retry count
            retry_count = 0
            while (1):
                # a dict with header and data as key
                user = receive_message(client_socket=client_socket)
                # clients.append(client_socket) need to auth before adding

                # If False client disconnected before sending credentials
                if user is False:
                    continue

                # print(user['data'].decode()) # "username,password"
                credentials = user['data'].decode().split(',')
                # print(credentials[0]) # username
                # print(credentials[1]) # password   

                # --- block_duration start ---
                check = None
                # check blocked account
                for blocked in blocked_clients:
                    if blocked_clients[blocked]['data'].decode() == credentials[0]:
                        username = blocked_clients[blocked]['data'].decode() #.split(',')[0]
                        # check block duration by doing current time - block duration
                        current_time = datetime.datetime.now()
                        minus_blocked = current_time - datetime.timedelta(seconds=block_duration)
                        if minus_blocked > blocked_clients[blocked]['account-blocked'] or minus_blocked == blocked_clients[blocked]['account-blocked']:
                            #FIXME uncomment debugging print before submitting
                            print(f'UNBLOCKED: {username}\'s account!')
                            if username == credentials[0]:
                                message = 'Your account have been unblocked since {}, {}!'.format(current_time.strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3], username).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)

                                # remove unblocked socket from list of blocked clients
                                del blocked_clients[blocked]
                                break
                        elif minus_blocked < blocked_clients[blocked]['account-blocked']:
                            check = username
                            if username == credentials[0]:
                                #FIXME uncomment debugging print before submitting
                                print(f'BLOCKED: {username} is still blocked!')
                                message = 'Your account is blocked {}. Please try again after {}!'.format(username, (blocked_clients[blocked]['account-blocked'] + datetime.timedelta(seconds=block_duration)).strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)
                                break
                #FIXME uncomment debugging print before submitting
                # print(f'Number of blocked clients: {len(list(blocked_clients))}')
                # if user tries to login after block with new client_socket
                if check == credentials[0]:
                    break
                # --- block_duration end ---

                # --- Check duplicate login start ---
                if user_exists_On9clients(username=credentials[0], on9clients=online_clients):
                    #FIXME uncomment debugging print before submitting
                    # print(f'AUTHENTICATION :{credentials[0]} is already online. FAILED!')
                    message = f'{credentials[0]} is already online!'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                    break
                # --- Check duplicate login end ---

                # --- authentication start ---
                result = authenticate(credential=credentials)

                #FIXME uncomment debugging print before submitting
                # print(f'AUTHENTICATION for {credentials[0]}: {result}')
                if 'Successful' in result:
                    # Add accepted socket to select() list
                    sockets_list.append(client_socket)

                    # just store username instead of username,password
                    user['data'] = user['data'].decode().split(',')[0].encode()
                    # update user header
                    user['header'] = f"{len(user['data']):<{20}}".encode()
                    # to check whoelsesince function
                    user['logged-in'] = datetime.datetime.now()
                    # to check user inactivity - timeout
                    user['last-active'] = user['logged-in']
                    # to connect p2p functions
                    user['private-connection'] = client_address

                    # user will have keys: header, data, logged-in, last-active
                    online_clients[client_socket] = user

                    print('Accepted new connection from {}:{} [{}]\n'.format(*client_address, user['data'].decode()))

                    # send login date time
                    message = 'Welcome back {}! You Logged in at: {}'.format(user['data'].decode(), user['logged-in'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                    break
                elif 'Password' in result:
                    retry_count += 1
                    if retry_count >= 3:
                        #FIXME uncomment debugging print before submitting
                        # print('BLOCKED: {}\'s account. Retry count :{}'.format(credentials[0], retry_count))
                        
                        # user will have username, user_header and block duration
                        user['data'] = credentials[0].encode()
                        # to keep track of block duration
                        user['account-blocked'] = datetime.datetime.now()
                        # add user to blocked account list
                        blocked_clients[client_socket] = user

                        message = 'Invalid Password. Retry count limit reached. Please try again later after {}. {}, Your account has been blocked!'.format((user['account-blocked'] + datetime.timedelta(seconds=block_duration)).strftime("%H:%M:%S.%f")[:-3], credentials[0]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        client_socket.send(message_header + message)
                        break
                    else:
                        result = result + ' retry count: {}'.format(retry_count)
                        message = result.encode()
                        message_header = f"{len(message):<{20}}".encode()
                        client_socket.send(message_header + message)
                # Invalid username
                else:
                    message = result.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                # --- authentication end ---
        # Else existing socket is sending a message
        # After authentication successful, server start to send user and message (both with their headers)
        # server will reuse message header sent by sender for certain commands like message, broadcasting, etc
        elif notified_socket in online_clients:

            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(online_clients[notified_socket]['data'].decode()))

                # add to offline user list
                if notified_socket not in offline_clients:
                    offline_clients[notified_socket] = user

                # Remove from list for sockets list
                sockets_list.remove(notified_socket)
                # Remove from list of online users
                del online_clients[notified_socket]

                continue

            # retrive user from list of online clients
            user = online_clients[notified_socket]

            if user is False:
                continue

            # --- timeout start ---
            current_time = datetime.datetime.now()
            minus_timeout = current_time - datetime.timedelta(seconds=timeout)
            if minus_timeout == user['last-active'] or minus_timeout > user['last-active']:
                print('Connection timeout for: {} since {}'.format(user['data'].decode().split(',')[0], (user['last-active'] + datetime.timedelta(seconds=timeout)).strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]))
                server = 'WICKWICK\'S SERVER'.encode()
                server_header = f"{len(server):<{20}}".encode()
                message = 'Connection timeout at {} due to inactivity. Bye {}!'.format((user['last-active'] + datetime.timedelta(seconds=timeout)).strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3], user['data'].decode()).encode()
                message_header = f"{len(message):<{20}}".encode()
                timeout_socket.send(server_header + server + message_header + message)

                # add to offline list
                offline_clients[notified_socket] = user

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del online_clients[notified_socket]

                # send indication of termination to client
                timeout_socket.shutdown(SHUT_RDWR)
                timeout_socket.close()
                continue
            # --- timeout end ---

            # update user's last active
            user['last-active'] = datetime.datetime.now()

            print('Received message at {} from {}: {}'.format(user['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3], user["data"].decode(), message["data"].decode()))

            # --- Commands start ---
            command = message["data"].decode().split(' ')[0]
            # --- broadcast start ---
            # if command == 'broadcast':

            # --- default ---
            # else:
                #FIXME uncomment debugging print before submitting
            print('FAIL: Invalid Command, {}!'.format(user['data'].decode()))
            message = 'Error, Invalid Command, {}!'.format(user['data'].decode()).encode()
            message_header = f"{len(message):<{20}}".encode()
            notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- Commands end ---
            # P2P in that elif notified_socket in online_clients
            # if len(clients) == 2:
            #     print("Two clients have connected. Exchanging details for P2P")
            #     clients[0].send(tupleToDelimString(clients[1].getpeername()).encode())
            #     clients[1].send(tupleToDelimString(clients[0].getpeername()).encode())
    time.sleep(1)

print("Server connection closed!")
sys.exit()