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
from select import *
import errno
import sys

# for easy testing uncomment this
server_name = 'localhost'
server_port = 12000

# FIXME before submitting
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

# --- P2P init ---
# create a socket
p2p_socket = socket(AF_INET, SOCK_STREAM)

# ensures that socket resuse is setup BEFORE it is bound. Will avoid the TIME_WAIT issue
p2p_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# p2p_socket.bind((server_name, server_port))
p2p_socket.bind((client_socket.getsockname()[0], client_socket.getsockname()[1]))

p2p_socket.listen()

# List of client_ socket and p2p_socket sockets for select()
sockets_list = [client_socket, p2p_socket]

# List of connected clients - socket as a key, user header and credentials as data
p2p_clients = {}

print(f'my addr: {server_name} : {server_port}')

print(f'client_socket to receive from server: {client_socket.getsockname()[0]} : {client_socket.getsockname()[1]}')

print(f'p2p_socket: {p2p_socket.getsockname()[0]} : {p2p_socket.getsockname()[1]}')

# --- Authentication START ---
username = input("Username: ").strip() # .replace(" ", "")
password = input("Password: ").strip() # .replace(" ", "")
credentials = username + ',' + password
print("You Entered >> user: " + username + ' and pwd: ' + password)
username = username.encode()
credentials = credentials.encode()
user_header = f"{len(credentials):<{20}}".encode()
# print(user_header+username)
# print(credentials.decode())
client_socket.send(user_header + credentials)

Logged = False

while (1): 
    # TODO p2p
    read_sockets, _, exception_sockets = select(sockets_list, [], sockets_list)

    if Logged != True:
        try:
            while (1):
                if Logged == True:
                    break

                user_header = client_socket.recv(20)

                user_length = int(user_header.decode())
                message = client_socket.recv(user_length).decode()
                print(message)
                if 'Welcome' in message:
                    print(f'----- {username.decode()}\'s console -----')
                    sockets_list.append(client_socket)
                    Logged = True
                    # break
                elif 'Logged out' in message:
                    # exit successfully
                    sys.exit(0)
                elif ('blocked' in message and username.decode() in message) or 'timeout' in message or 'already online!' in message:
                    # exit forced
                    sys.exit(1)
                elif 'Password' in message:
                    username = username.decode()
                    password = input("Password: ").strip() # .replace(" ", "")
                    credentials = username + ',' + password
                    print("You Entered >> user: " + username + ' and pwd: ' + password)
                    credentials = credentials.encode()
                    user_header = f"{len(credentials):<{20}}".encode()
                    # print(user_header+username)
                    # print(credentials.decode())
                    username = username.encode()
                    client_socket.send(user_header + credentials)
                elif 'Username' in message:
                    username = input("Username: ").strip() # .replace(" ", "")
                    password = input("Password: ").strip() # .replace(" ", "")
                    credentials = username + ',' + password
                    print("You Entered >> user: " + username + ' and pwd: ' + password)
                    username = username.encode()
                    credentials = credentials.encode()
                    user_header = f"{len(credentials):<{20}}".encode()
                    # print(user_header+username)
                    # print(credentials.decode())
                    client_socket.send(user_header + credentials)

        except IOError as e:
            # This is normal on non blocking connections - when there are no incoming data error is going to be raised
            # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
            # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
            # If we got different error code - something happened
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
                sys.exit(1)
            # We just did not receive anything
            continue

        except Exception as e:
            # Any other exception - something happened, exit
            print('Reading error: Authentication FAIL: message(s) from server'.format(str(e)))
            sys.exit(1)
    # --- Authentication END ---
    while (1):

        for notified_socket in read_sockets:

            # new connections to p2p socket
            if notified_socket is p2p_socket:
                print("p2p !?")
                p2p_client, p2p_address = p2p_socket.accept()
                data = None
                try:
                    user_header = p2p_client.recv(20)

                    # if not len(user_header):

                    header_length = int(user_header.decode())

                    data = {'header': user_header, 'data': p2p_socket.recv(header_length)}

                    message_header = p2p_clients.recv(20)
                    message_length = int(message_header.decode())
                    message = p2p_clients.recv(message_length).decode()
                except:
                    data = None

                # private_user = data

                # if private_user != None:
                #     print(message)

                #     sockets_list.append(p2p_client)

                #     p2p_clients[notified_socket] = private_user
                #     print('Accepted new connection from {}:{}, sender: {}'.format(*p2p_address, private_user['data'].decode().split(',')[0]))
                #     message = '{} Accepted your PRIVATE connection, {}'.format(username.decode(), private_user['data'].decode().split(',')[0]).encode()
                #     message_header = f"{len(message):<{20}}".encode()
                #     p2p_clients.send(user_header + credentials + message_header + message)
                # else:
                #     # sockets_list.remove(notified_socket)
                #     print('Failed to accept new connection from {}:{}, sender: {}'.format(*p2p_address, private_user['data'].decode().split(',')[0]))
                #     message = '{} Failed to accept your PRIVATE connection, {}'.format(username.decode(), private_user['data'].decode().split(',')[0]).encode()
                #     message_header = f"{len(message):<{20}}".encode()
                #     p2p_clients.send(user_header + credentials + message_header + message)
            
            # server need to return user + message
            # --- Receive message from server start ---
            # TODO add
            elif notified_socket is client_socket:
                # FIXME Wait for user to input a message
                my_input = input(f'{username.decode()} > ').strip()

                # If message is not empty - send it
                if my_input:
                    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
                    message = my_input.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                try:
                    # Now we want to loop over received messages (there might be more than one) and print them
                    while (1):
                        # Receive our "header" containing user length, it's size is defined and constant
                        user_header = client_socket.recv(20)

                        # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                        if not len(user_header):
                            print('Connection closed by the server')
                            sys.exit(1)

                        # Convert header to int value
                        user_length = int(user_header.decode())

                        # Receive and decode message
                        user = client_socket.recv(user_length).decode().split(',')[0]

                        # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                        message_header = client_socket.recv(20)
                        message_length = int(message_header.decode())
                        message = client_socket.recv(message_length).decode()

                        # Print message
                        if 'WICKWICK\'S SERVER' is user or 'Logged' in message:
                            print(message)
                        elif 'Connecting' in message:
                            address = (message.split(' ',1)[1]).split(' ')
                            print(type(address))
                            print(f'Attempt to connect {address[0]} : {address[1]}')
                            new_socket = socket(AF_INET, SOCK_STREAM)
                            new_socket.connect((address[0],int(address[1])))
                            new_socket.setblocking(False)

                            # print("done")
                            # user_header = f"{len(user.encode()):<{20}}".encode()
                            # new_socket.send(user_header + user.encode())
                            # break
                            # print("done")
                            # print("Fail to accept connection, already have one conn")
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

            # else:
            #     print("hi2")
                # # If message is not empty - send it
                # if message:
                #     # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
                #     user_header = f"{len(username):<{20}}".encode()
                #     message = message.encode()
                #     message_header = f"{len(message):<{20}}".encode()
                #     p2p_socket.send(user_header + username + message_header + message)
                # try:
                #     # Now we want to loop over received messages (there might be more than one) and print them
                #     while (1):

                #         # Receive our "header" containing user length, it's size is defined and constant
                #         user_header = p2p_socket.recv(20)

                #         # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                #         if not len(user_header):
                #             print('Connection closed by the p2p')
                #             sys.exit(1)

                #         # Convert header to int value
                #         user_length = int(user_header.decode())

                #         # Receive and decode message
                #         user = client_socket.recv(user_length).decode() #.split(',')[0]

                #         # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                #         message_header = p2p_socket.recv(20)
                #         message_length = int(message_header.decode())
                #         message = p2p_socket.recv(message_length).decode()

                #         # Print message
                #         if 'Accepted' in message or 'Failed' in message:
                #             print(message)
                #         else:
                #             print(f'PRIVATE MSG from {user} > {message}')

                # except IOError as e:
                #     # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                #     # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                #     # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                #     # If we got different error code - something happened
                #     if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                #         print('Reading error: {} at p2p_socket'.format(str(e)))
                #         sys.exit(1)
                #     # We just did not receive anything
                #     continue

                # except Exception as e:
                #     # Any other exception - something happened, exit
                #     print('Reading error: Message FAIL: message(s) from p2p'.format(str(e)))
                #     sys.exit(1)

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from online list of users
        del p2p_clients[notified_socket]

