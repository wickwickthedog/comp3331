'''
Used the sample code as reference from 
https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/?completed=/server-chatroom-sockets-tutorial-python-3/
also combining the code from server to here
Coding: utf-8, Python 3
Author: z5147986, wickwickthedog
Usage: 
(default) - pyhton3 client.py <host> <port>
'''
from socket import *
from select import *
from utility import receive_message
import errno
import sys
import time

server_name = 'localhost'
server_port = 12000

# FIXME before submitting
# server_name = sys.argv[1]
# server_port = int(sys.argv[2])

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

online_p2p_clients = {}

# --- Authentication START ---
username = input("Username: ").strip() # .replace(" ", "")
password = input("Password: ").strip() # .replace(" ", "")
credentials = username + ',' + password
print(f'Entered >> username:{username} and pwd: {password}')
username = username.encode()
credentials = credentials.encode()
user_header = f"{len(credentials):<{20}}".encode()
client_socket.send(user_header + credentials)

while (1):
    read_sockets, _, _ = select(socket_list, [], [], 1)
    
    for notified_socket in read_sockets:
        # p2p
        if notified_socket is p2p_socket:
            p2p_client, p2p_address = p2p_socket.accept()
            print(f'p2p_client: {p2p_client.getsockname()}')
            socket_list.append(p2p_client)
            p2p_user = {}
            p2p_user['username'] = username
            p2p_user['address'] = p2p_address
            # print('p2p_user: {}'.format(p2p_user['username']))
            online_p2p_clients[p2p_client] = p2p_user
            # print('online_p2p_clients[p2p_client]: {}'.format(online_p2p_clients[p2p_client]['username']))
            message = 'with ~ {} @ {}'.format(p2p_user['username'].decode(), p2p_user['address']).encode()
            message_header = f"{len(message):<{20}}".encode()
            p2p_client.send(message_header + message)
            
            print('P2P ~ Accepted new connection from {}'.format(p2p_address))

            # message = 'private-successful ~ {}'.format(username.decode()).encode()
            # message_header = f"{len(message):<{20}}".encode()
            # client_socket.send(message_header + message)
        elif notified_socket in online_p2p_clients:
            # time.sleep(.5)
            message = receive_message(client_socket=notified_socket)

            if not message:
                print('p2p_client: {} was closed.'.format(online_p2p_clients[notified_socket]['username'].decode()))
                socket_list.remove(notified_socket)
                del online_p2p_clients[notified_socket]
            else:
                print('P2P {} > {}'.format(online_p2p_clients[notified_socket]['username'].decode(), message['data'].decode()))
                message = 'private-successful ~ {}'.format(username.decode()).encode()
                message_header = f"{len(message):<{20}}".encode()
                client_socket.send(message_header + message)
        # server
        elif notified_socket is client_socket:
                # --- authentication start ---
                while not Logged_in:
                    message = receive_message(client_socket=notified_socket)

                    # If False server disconnected before sending message
                    if message is False:
                        continue
                    result = message['data'].decode()
                    if 'offline messages successful, ' in result:
                        Logged_in = True
                        continue
                    else:
                        print(result)
                    if 'Welcome' in result:
                        # Logged_in = True
                        continue
                    elif 'unblocked' in result:
                        continue
                    elif 'blocked' in result or 'already online' in result or 'timeout' in result:
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
                is_private = False
                # sent = False
                # Now we want to loop over received messages (there might be more than one) and print them
                while (1):
                    if is_private:
                        break
                    # time.sleep(.30)
                    command = input(f'{username.decode()} > ').strip()
                    time.sleep(.15)
                    if command is not'':
                    #     message = command.encode()
                    #     message_header = f"{len(message):<{20}}".encode()
                    # else:
                        check = command.split(' ')
                        if check[0] == 'private':
                            if len(check) < 3:
                                print(f'Error, Insufficient Args! {check[1]}')
                            else:
                                sent = False
                                for client_socket in online_p2p_clients:
                                    # print('{} & {}'.format(online_p2p_clients[client_socket]['username'].decode(), check[1]))
                                    if online_p2p_clients[client_socket]['username'].decode() == check[1]:
                                    # if client_socket == notified_socket:
                                        # send message
                                        message = command.split(' ',2)[2].encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        client_socket.send(message_header + message)
                                        # print('sent')
                                        message = 'private-notification {}'.format(check[1]).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(message_header + message)
                                        sent = True
                                        break
                                # startprivate not init
                                if not sent:
                                    print(f'Error, Private messaging to {check[1]} not enabled yet!')
                        else:
                            message = command.encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(message_header + message)
                            time.sleep(.15)
                    try:
                        while (1):
                            # need this else need to press enter to get the message
                            time.sleep(.85)
                            # receive "header" containing user length, it's size is defined and constant
                            user_header = notified_socket.recv(20)

                            # if we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                            if not len(user_header):
                                print('Connection closed by the server')
                                sys.exit(1)

                            # convert header to int value
                            user_length = int(user_header.decode())

                            # receive and decode message
                            user = notified_socket.recv(user_length).decode()

                            # now do the same for message (as we received username, 
                            # we received whole message, there's no need to check if it has any length)
                            message_header = notified_socket.recv(20)
                            message_length = int(message_header.decode())
                            message = notified_socket.recv(message_length).decode()

                            # print message
                            if 'WICKWICK\'S SERVER' in user or f'Logged out successful at ' in message:
                                print(message)
                                # send indication of termination to client
                                notified_socket.shutdown(SHUT_RDWR)
                                notified_socket.close()
                                sys.exit(1)
                            elif f'No command specified, {user}!' in message or f'successful, {user}!' in message:
                                break
                            elif f'Logged in at ' in message or f'{user} Logged out at ' in message or 'Error,' in message:
                                print(message)
                                break
                            elif 'whoelse ' in message:
                                client_count = int(message.split(' ')[1])
                                print(f'Number of online clients: {client_count}')
                            elif 'startprivate' in message:
                                if message == 'startprivate':
                                    is_private = True
                                    break
                                commands = message.split(' ')
                                # client
                                print(f'Attempt to connect {commands[1]} : {commands[2]}')
                                new_socket = socket(AF_INET, SOCK_STREAM)
                                new_socket.connect((commands[1], int(commands[2])))
                                new_socket.setblocking(False)
                                print(f'new_socket: {new_socket.getsockname()}')

                                recipient = {}
                                recipient['username'] = commands[3].encode()

                                online_p2p_clients[new_socket] = recipient
                                # print('recipient {}'.format(online_p2p_clients[new_socket]['username']))
                                socket_list.append(new_socket)
                                is_private = True
                                # print(online_p2p_clients)
                                break
                            else:
                                print(f'{user} > {message}')
                    except IOError as e:
                        # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                        # If we got different error code - something happened
                        # print("i am here")
                        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                            print('Reading error: {} at client_socket'.format(str(e)))
                            sys.exit(1)
                        # We just did not receive anything
                        continue

                    except Exception as e:
                        # Any other exception - something happened, exit
                        print('Reading error: Message FAIL: message(s) from server'.format(str(e)))
                        sys.exit(1)
                # --- Receive message from server end ---
        # elif notified_socket is not client_socket:
        else:
            message = receive_message(client_socket=notified_socket)

            if not message:
                print('Connection {} was closed.'.format(notified_socket.getsockname()))
                socket_list.remove(notified_socket)
            else:
                print('P2P {}'.format(message['data'].decode()))
                message = 'private-successful ~ {}'.format(username.decode()).encode()
                message_header = f"{len(message):<{20}}".encode()
                client_socket.send(message_header + message)
    time.sleep(1)