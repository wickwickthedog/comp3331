'''
Used the sample code as reference from 
https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/?completed=/server-chatroom-sockets-tutorial-python-3/
also combining the code from server to here
Coding: utf-8, Python 3
Editted by: z5147986
Usage: 
(default) - pyhton3 client.py <host> <port>
'''
from socket import *
from select import *
from utility import receive_message, receive_messages
import errno
import sys
import time
import datetime

# server_name = 'localhost'
# server_port = 12000

# FIXME before submitting
server_name = sys.argv[1]
server_port = int(sys.argv[2])

# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, notified_socketless, messagegrams, socket.SOCK_RAW - raw server_name packets
client_socket = socket(AF_INET, SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
# ensures that socket resuse is setup BEFORE it is bound. Will avoid the TIME_WAIT issue
client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Connect to a given server_name and server_port
client_socket.connect((server_name, server_port))

# Set notified_socket to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
client_socket.setblocking(False)

# --- P2P init ---
# create a socket
p2p_socket = socket(AF_INET, SOCK_STREAM)

# ensures that socket resuse is setup BEFORE it is bound. Will avoid the TIME_WAIT issue
p2p_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# p2p_socket.bind((server_name, server_port))
p2p_socket.bind((client_socket.getsockname()[0], client_socket.getsockname()[1]))

p2p_socket.listen()

# List of client_ socket and p2p_socket sockets for select()
socket_list = [client_socket, p2p_socket]

print(f'Connecting to server at {server_name} : {server_port}')
print(f'client_socket to receive from server: {client_socket.getsockname()[0]} : {client_socket.getsockname()[1]}')
print(f'p2p_socket: {p2p_socket.getsockname()[0]} : {p2p_socket.getsockname()[1]}\n')

Logged_in = False

# List of p2p client sockets created
# contains client-owner, server-owner
online_p2p_clients = {}

# List of p2p clients connected to my p2p server
# contains client-owner
online_p2p_servers = {}

# --- Authentication START ---
username = input("Username: ").strip() # .replace(" ", "")
password = input("Password: ").strip() # .replace(" ", "")
credentials = username + ',' + password
print(f'Entered >> username:{username} and pwd: {password}')
username = username.encode()
credentials = credentials.encode()
user_header = f"{len(credentials):<{20}}".encode()
client_socket.send(user_header + credentials)

command = ''
is_private = False
while (1):
    if not is_private: # too make the p2p connection smooth without input interruption
        if Logged_in:
            command = input(f'{username.decode()} > ').strip()
            if command is not '':
                commands = command.split(' ')
                if 'private' == commands[0]:
                    if len(commands) < 3:
                        print(f'Error, Insufficient Args!')
                    elif commands[1] == username.decode():
                        print(f'Error, can\'t private self!')
                    else:
                        sent = False
                        for client_socket in online_p2p_clients:
                            # print(online_p2p_clients[client_socket]['server-owner'])
                            if online_p2p_clients[client_socket]['server-owner'] == commands[1]:
                                message = command.split(' ', 2)[2].encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)
                                sent = True
                                print(f'p2p message sent to {commands[1]}!')
                                break
                        if not sent:
                            print(f'Error, Private messaging to {commands[1]} not enabled yet!')
                elif 'stopprivate' == commands[0]:
                    if len(commands) > 2 or len(commands) < 2:
                        print(f'Error, Too many Args or Insufficient Args!')
                    elif commands[1] == username.decode():
                        print(f'Error, can\'t stopprivate self!')
                    else:
                        closed = False
                        for client_socket in online_p2p_clients:
                            if online_p2p_clients[client_socket]['server-owner'] == commands[1]:
                                message = 'stopprivate is activated by {} !'.format(online_p2p_clients[client_socket]['client-owner']).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)
                                # client_socket.shutdown(SHUT_RDWR)
                                client_socket.close()
                                closed = True
                                # remove p2p client
                                del online_p2p_clients[client_socket]
                                # socket_list.remove(client_socket)
                                print(f'Your p2p client to {commands[1]} is removed at {datetime.datetime.now()}')
                                break
                        if not closed:
                            print(f'Error, Private messaging to {commands[1]} not enabled yet!')
                else:
                    try:
                        message = command.encode()
                        message_header = f"{len(message):<{20}}".encode()
                        client_socket.send(message_header + message)
                        time.sleep(.5)
                    except:
                        # connection timeout
                        continue

    read_sockets, _, _ = select(socket_list, [], [], 1)

    for notified_socket in read_sockets:
        # p2p init
        if notified_socket is p2p_socket:
            p2p_client, p2p_address = p2p_socket.accept()
            socket_list.append(p2p_client)

            current_time = datetime.datetime.now()

            print('P2P ~ Accepted new connection from {} at {}'.format(p2p_address, current_time))
            is_private = True

        # p2p incoming messages 
        elif notified_socket in online_p2p_servers:
            message = receive_message(client_socket=notified_socket)

            if not message:
                print('p2p_client: {} was closed.'.format(online_p2p_servers[notified_socket]['client-owner']))
                socket_list.remove(notified_socket)
                # remove p2p clients from my p2p server
                del online_p2p_servers[notified_socket]
            else:
                msg = message['data'].decode().split(' ')
                # print(msg)
                if msg[0] == 'stopprivate':
                    print(message['data'].decode())
                    # notified_socket.shutdown(SHUT_RDWR)
                    notified_socket.close()
                    for client_socket in online_p2p_clients:
                        if msg[4] == online_p2p_clients[client_socket]['server-owner']:
                            # remove p2p client
                            del online_p2p_clients[client_socket]
                            break
                    socket_list.remove(notified_socket)
                else:
                    print('P2P {} > {}'.format(online_p2p_servers[notified_socket]['client-owner'], message['data'].decode()))

        # server
        elif notified_socket is client_socket and not Logged_in:
            # --- authentication start ---
            while not Logged_in:
                message = receive_message(client_socket=notified_socket)

                # If False server disconnected before sending message
                if message is False:
                    continue
                result = message['data'].decode()

                # display all offline messages
                if 'offline messages successful, ' in result:
                    Logged_in = True
                else:
                    print(result)

                if 'Welcome' in result or 'unblocked' in result:
                    continue
                elif 'blocked' in result or 'already online' in result:
                    # send indication of termination
                    client_socket.shutdown(SHUT_RDWR)
                    client_socket.close()
                    sys.exit(1)
                elif 'Password' in result:
                    password = input("Password: ").strip() # .replace(" ", "")
                    credentials = username.decode() + ',' + password
                    print(f'Entered >> username:{username} and pwd: {password}')
                    credentials = credentials.encode()
                    user_header = f"{len(credentials):<{20}}".encode()
                    notified_socket.send(user_header + credentials)
                elif 'Username' in result:
                    username = input("Username: ").strip() # .replace(" ", "")
                    password = input("Password: ").strip() # .replace(" ", "")
                    credentials = username + ',' + password
                    print(f'Entered >> username:{username} and pwd: {password}')
                    username = username.encode()
                    credentials = credentials.encode()
                    user_header = f"{len(credentials):<{20}}".encode()
                    notified_socket.send(user_header + credentials)
            # --- authentication end ---
        
        # --- Receive message from server start ---
        elif notified_socket is client_socket and Logged_in:
            
            is_private = False
            while not is_private:
                # time.sleep(.5)
                msg = receive_messages(client_socket=notified_socket)
                 # did not receive anything
                if msg is False:
                    continue

                user = str(msg['header'])
                message = msg['data']

                # print message
                if f'Logged out successful at ' in message:
                    print(message)
                    # send indication of termination to server
                    notified_socket.shutdown(SHUT_RDWR)
                    notified_socket.close()
                    socket_list.remove(notified_socket)
                    sys.exit(1)
                elif 'WICKWICK\'S SERVER' == user: # timeout don't close since possible p2p
                    print(message)
                    notified_socket.shutdown(SHUT_RDWR)
                    notified_socket.close()
                    socket_list.remove(notified_socket)
                    break
                elif f'successful, {user}!' in message:
                    break
                elif 'Error,' in message: 
                    print(message)
                    break
                elif f'Logged in at ' in message or f'{user} Logged out at ' in message or 'sent offline message to: ' in message:
                    print(message)
                    break
                elif 'blocked ' in message or 'unblocked ' in message or 'Some user will not get the broadcast!' == message:
                    print(message)
                elif 'whoelse ' in message:
                    client_count = int(message.split(' ')[1])
                    print(f'Number of online clients: {client_count}')
                elif ' is online!' in message or 'online, last active: ' in message:
                    print(message)
                elif 'to accept your connection...' in message:
                    print(message)
                elif 'startprivate' in message:
                    commands = message.split(' ')
                    print(f'Attempting to connect {commands[1]} : {commands[2]}')
                    new_socket = socket(AF_INET, SOCK_STREAM)
                    new_socket.connect((commands[1], int(commands[2])))
                    new_socket.setblocking(False)
                    print(f'new_socket: {new_socket.getsockname()}')

                    p2p_user = {}
                    p2p_user['client-owner'] = commands[3]
                    p2p_user['server-owner'] = commands[4]
                    #FIXME uncomment debugging print before submitting
                    # print(f'3 is me: {commands[3]}')

                    # my online p2p clients to other p2p servers
                    online_p2p_clients[new_socket] = p2p_user
                    is_private = True

                    message = f'p2p {commands[3]} : setup to {commands[4]} successful!'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    new_socket.send(message_header + message)
                else:
                    print(f'{user} > {message}')
                    break
        # --- Receive message from server end ---

        # --- Receive message from p2p to setup --- 
        else:
            message = receive_message(client_socket=notified_socket)

            if not message:
                print('A p2p client was closed.')
                socket_list.remove(notified_socket)
                # remove p2p clients from my p2p server
                # del online_p2p_servers[notified_socket]
            else:
                msg = message['data'].decode()
                p2p_user = {}
                if len(msg) > 5:
                    p2p_user['client-owner'] = msg.split(' ')[4]
                    # p2p clients that are online in my p2p server
                    online_p2p_servers[p2p_client] = p2p_user
                print(msg)
                is_private = False
                #FIXME uncomment debugging print before submitting
                # print(online_p2p_servers)
                # print(online_p2p_clients)
    # time.sleep(.5)