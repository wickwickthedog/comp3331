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
from utility import authenticate, user_exists, check_blocked
import sys
import datetime 

# for easy testing uncomment this
server_host = 'localhost'
server_port = 12000
block_duration = 60
timeout = 120

# FIXME
# for easy testing comment this
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

# list of offline messages
offline_messages = {}

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
                logged_out_clients[timeout_socket] = clients[timeout_socket]

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

                # FIXME --- Check duplicate login---
                # exist = False
                # dup = None
                # for exist_socket in clients:
                #     if credentials[0] in clients[exist_socket]['data'].decode():
                #         exist = True
                #         dup = exist_socket
                #         break

                # --- Authentication start ---
                # if exist == False:
                result = authenticate(credentials)

                print(f'AUTHENTICATION for {credentials[0]}: {result}')
                if 'Successful' in result:

                    # Add accepted socket to select() list
                    sockets_list.append(client_socket)

                    # to check user inactivity - timeout
                    user['last-active'] = datetime.datetime.now()
                    # user will have user_header and credentials
                    clients[client_socket] = user

                    username = user['data'].decode().split(',')[0]
                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, username))
                    # client_socket.send(f'Welcome {username}'.encode())

                    message = '--------------------------'.encode()
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

                    message = 'message <user> <messages>'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = '--------------------------'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = '---- offline messages ----'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    # print(client_socket)

                    # for client_socket in logged_out_clients:
                    #     if logged_out_clients[client_socket]['data'].decode().split(',')[0] == credentials[0]:
                    #         # print(offline_messages[client_socket]['recipient'].decode())
                    #         if credentials[0] == logged_out_clients[client_socket]['recipient'].decode():
                                # for msg in offline_messages:
                                #     if credentials[0] == offline_messages[client_socket]['recipient'].decode():
                                #         message = '{} > {}'.format(offline_messages[client_socket]['sender'].decode().split(',')[0], offline_messages[client_socket]['message'].decode()).encode()
                                #         message_header = f"{len(message):<{20}}".encode()
                                #         client_socket.send(message_header + message)
                    #             del offline_messages[client_socket]
                    #             break
                    # else:
                    #     message = '          None            '.encode()
                    #     message_header = f"{len(message):<{20}}".encode()
                    #     client_socket.send(message_header + message)

                    # update logged out clients list and send offline message(s)
                    for logged_out_socket in logged_out_clients:
                        if logged_out_clients[logged_out_socket]['data'].decode().split(',')[0] == credentials[0]:
                            if logged_out_socket in offline_messages:
                                for msg in offline_messages[logged_out_socket]:
                                    # print(offline_messages[msg])
                                    if credentials[0] == msg['recipient'].decode().split(',')[0]:
                                        message = '{} > {}'.format(msg['sender'].decode().split(',')[0], msg['message'].decode()).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        client_socket.send(message_header + message)
                                del offline_messages[logged_out_socket]
                            del logged_out_clients[logged_out_socket]
                            break

                    message = '------------------------'.encode()
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
                # else:
                #     message = f'blocked, {credentials[0]} already logged in!'.encode()
                #     message_header = f"{len(message):<{20}}".encode()
                #     client_socket.send(message_header + message)
                    # dup.send(message_header + message)
                    # client_socket.shutdown(SHUT_RDWR)
                # --- Authentication end ---

        # Else existing socket is sending a message
        elif notified_socket in clients and notified_socket not in blocked_clients:
        # else:
            
            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))

                # add to logged out list
                if notified_socket not in logged_out_clients:
                    logged_out_clients[notified_socket] = clients[notified_socket]

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            if user is False:
                continue

            user['last-active'] = datetime.datetime.now()

            print('Received message at {} from {}: {}'.format(user['last-active'], user["data"].decode().split(',')[0], message["data"].decode()))

            # --- TODO Commands start ---
            command = message["data"].decode().split(' ')[0]
            # --- broadcast start ---
            if command == 'broadcast':
                # try:
                check = message['data'].decode().split(' ')
                if len(check) >= 2:
                    message['data'] = message['data'].decode().split(' ', 1)[1].encode()
                    # Iterate over connected clients and broadcast message
                    exist = False
                    for client_socket in clients:
                        blocked = False
                        # But don't sent it to sender
                        if client_socket != notified_socket:
                            if 'blocked-user' in clients[notified_socket]:
                                # print(len(clients[notified_socket]['blocked-user']))
                                for i in range(len(clients[notified_socket]['blocked-user'])):
                                    if clients[client_socket]['data'] == clients[notified_socket]['blocked-user'][i]['data']:
                                        exist = True
                                        blocked = True
                                        break
                            if 'blocked-user' in clients[client_socket]:
                                # print(len(clients[client_socket]['blocked-user']))
                                for i in range(len(clients[client_socket]['blocked-user'])):
                                    if clients[notified_socket]['data'] == clients[client_socket]['blocked-user'][i]['data']:
                                        exist = True
                                        blocked = True
                                        break
                                # Send user and message (both with their headers)
                                # We are reusing here message header sent by sender, and saved username header send by user when he connected
                            if blocked == False:
                                client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                    if exist:
                        print('{} some user will not get the broadcast!'.format(user['data'].decode().split(',')[0]))
                        message = 'some user will not get the broadcast, {}!'.format(user['data'].decode().split(',')[0]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        break
                # except:
                else:
                    print('FAIL: No message to broadcast, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'No message to broadcast, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- broadcast end ---
            # --- whoelse start ---
            elif command == 'whoelse':
                check = message['data'].decode().split(' ')
                if len(check) == 1:
                    for client_socket in clients:
                        if client_socket != notified_socket and client_socket not in blocked_clients:
                            message = '{} is online!'.format(clients[client_socket]['data'].decode().split(',')[0]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    print('FAIL: whoelse need no args, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'whoelse need no args, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- whoelse end ---
            # --- whoelsesince start ---
            elif command == 'whoelsesince':
                # try:
                check = message['data'].decode().split(' ')
                if len(check) == 2:
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
                            if t > current_time:
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
                # except:
                else:
                    print('FAIL: No time specified, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'No time specified, {}'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- whoelsesince end ---
            # --- message start ---
            elif command == 'message':
                check = message['data'].decode().split(' ')
                if len(check) < 3:
                    print('FAIL: Insufficient Args, {}!'.format(clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args, {}!'.format(clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    if check[1] == user['data'].decode().split(',')[0]:
                        print('{} can\'t MESSAGE SELF!'.format(check[1]))
                        message = 'can\'t MESSAGE SELF: {}!'.format(check[1]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                    else:
                        recipient = message['data'].decode().split(' ')[1]
                        msg = message['data'].decode().split(' ', 2)[2]

                        if user_exists(recipient, clients, logged_out_clients):
                            for client_socket in clients:
                                if client_socket != notified_socket and clients[client_socket]['data'].decode().split(',')[0] == recipient:
                                    if check_blocked(notified_socket, clients):
                                        message = 'Error, can\'t send message to: {}!'.format(recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    else:
                                        msg = msg.strip().encode()
                                        message_header = f"{len(msg):<{20}}".encode()
                                        client_socket.send(user['header'] + user['data'] + message_header + msg)
                            for client_socket in logged_out_clients:
                                if client_socket != notified_socket and logged_out_clients[client_socket]['data'].decode().split(',')[0] == recipient:
                                    if not check_blocked(notified_socket, clients):
                                        msg = msg.strip().encode()
                                        # message_header = f"{len(msg):<{20}}".encode()
                                        # client_socket.send(user['header'] + user['data'] + message_header + msg)
                                        if client_socket in offline_messages:
                                            offline_messages[client_socket].append({'sender_header': user['header'], 'sender': user['data'], 'recipient': logged_out_clients[client_socket]['data'], 'message':msg })
                                        else:
                                            offline_messages[client_socket] = [{'sender_header': user['header'], 'sender': user['data'], 'recipient': logged_out_clients[client_socket]['data'], 'message':msg }]
                                    else:
                                        message = 'Error, can\'t send message to: {}!'.format(recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)

                        else:
                            print('FAIL: Invalid User: {}!'.format(recipient))
                            message = 'Error, Invalid User: {}!'.format(recipient).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- message end ---
            # --- block start ---
            elif command == 'block':
                check = message['data'].decode().split(' ')
                if len(check) == 2:
                    if check[1] == user['data'].decode().split(',')[0]:
                        print('{} can\'t BLOCK SELF!'.format(check[1]))
                        message = 'can\'t BLOCK SELF: {}!'.format(check[1]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)

                    elif user_exists(check[1], clients, logged_out_clients):
                        for client_socket in clients:
                            if client_socket != notified_socket and clients[client_socket]['data'].decode().split(',')[0] == check[1]:
                                
                                if 'blocked-user' not in clients[notified_socket]:
                                    clients[notified_socket]['blocked-user'] = [clients[client_socket]]
                                else:
                                    exist = False
                                    for i in range(len(clients[notified_socket]['blocked-user'])):
                                        if check[1] == clients[notified_socket]['blocked-user'][i]['data'].decode().split(',')[0]:
                                            print('{} already BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], check[1]))
                                            message = 'already BLOCKED USER: {}!'.format(check[1]).encode()
                                            message_header = f"{len(message):<{20}}".encode()
                                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                                            exist = True
                                            break
                                    if exist:
                                        # print(len(clients[notified_socket]['blocked-user']))
                                        break
                                    # print(len(clients[notified_socket]['blocked-user']))
                                    clients[notified_socket]['blocked-user'].append(clients[client_socket])
                                print('{} BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], clients[client_socket]['data'].decode().split(',')[0]))
                                message = 'BLOCKED USER: {}!'.format(clients[client_socket]['data'].decode().split(',')[0]).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                break
                        for client_socket in logged_out_clients:
                            if client_socket != notified_socket and logged_out_clients[client_socket]['data'].decode().split(',')[0] == check[1]:
                                if 'blocked-user' not in clients[notified_socket]:
                                    clients[notified_socket]['blocked-user'] = [logged_out_clients[client_socket]]
                                else:
                                    exist = False
                                    for i in range(len(clients[notified_socket]['blocked-user'])):
                                        if check[1] == clients[notified_socket]['blocked-user'][i]['data'].decode().split(',')[0]:
                                            print('{} already BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], check[1]))
                                            message = 'already BLOCKED USER: {}!'.format(check[1]).encode()
                                            message_header = f"{len(message):<{20}}".encode()
                                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                                            exist = True
                                            break
                                    if exist:
                                        # print(len(clients[notified_socket]['blocked-user']))
                                        break
                                    clients[notified_socket]['blocked-user'].append(logged_out_clients[client_socket])
                                print('{} BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], logged_out_clients[client_socket]['data'].decode().split(',')[0]))
                                message = 'BLOCKED USER: {}!'.format(logged_out_clients[client_socket]['data'].decode().split(',')[0]).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                break
                    else:
                        print('FAIL: {} doesn\'t exist!'.format(check[1]))
                        message = 'Error, {} doesn\'t exist!'.format(check[1]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    print('FAIL: Insufficient Args: {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args: {}!'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- block end ---
            # --- unblock start ---
            elif command == 'unblock':
                check = message['data'].decode().split(' ')
                if len(check) == 2:
                    if check[1] == user['data'].decode().split(',')[0]:
                        print('{} can\'t UNBLOCK SELF!'.format(check[1]))
                        message = 'can\'t UNBLOCK SELF: {}!'.format(check[1]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        break

                    # print(len(list(clients[notified_socket]['blocked-user'])))
                    for client_socket in clients:
                        if 'blocked-user' in clients[notified_socket]:
                            for i in range(len(clients[notified_socket]['blocked-user'])):
                                if check[1] == clients[notified_socket]['blocked-user'][i]['data'].decode().split(',')[0]:
                                    print('{} UNBLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], check[1]))
                                    message = 'UNBLOCKED USER: {}!'.format(check[1]).encode()
                                    message_header = f"{len(message):<{20}}".encode()
                                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    del clients[notified_socket]['blocked-user'][i]
                                    break
                            # for blocked in list(clients[notified_socket]['blocked-user']):
                            #     print(blocked)
                            #     if check[1] == blocked['data'].decode().split(',')[0]: #and blocked['data'] == clients[client_socket]['data']:
                            #         print('{} UNBLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], check[1]))
                            #         message = 'UNBLOCKED USER: {}!'.format(check[1]).encode()
                            #         message_header = f"{len(message):<{20}}".encode()
                            #         notified_socket.send(user['header'] + user['data'] + message_header + message)
                            #         del blocked
                            #         break
                        else:
                            print('FAIL: to unblock: {}!'.format(check[1]))
                            message = 'Error, fail to unblock {}!'.format(check[1]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                            break
                else:
                    print('FAIL: Insufficient Args: {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args: {}!'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- unblock end ---
            # --- default ---
            else:
                print('FAIL: Invalid Command, {}!'.format(user['data'].decode().split(',')[0]))
                message = 'Error, Invalid Command, {}!'.format(user['data'].decode().split(',')[0]).encode()
                message_header = f"{len(message):<{20}}".encode()
                notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- Commands end ---

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]