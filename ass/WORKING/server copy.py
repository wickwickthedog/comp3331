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
from utility import authenticate, user_exists_On9clients, user_exists_Off9clients, user_exists, user_blocked
import sys
import datetime 

# for easy testing uncomment this
server_host = 'localhost'
server_port = 12000
block_duration = 60
timeout = 120

# FIXME before submitting
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
# ensures that socket resuse is setup BEFORE it is bound. Will avoid the TIME_WAIT issue
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given server_host and server_port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface server_host
server_socket.bind((server_host, server_port))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and credentials as data
online_clients = {}

# list of blocked clients
blocked_clients = {}

# list of offline clients
offline_clients = {}

# list of offline messages
offline_messages = {}

print(f'Listening for connections on {server_host}:{server_port}')

# Handles message receiving
def receive_message(client_socket):
    try:
        # Receive header containing message length, it's size is defined as 20
        message_header = client_socket.recv(20)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

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
    for timeout_socket in list(online_clients):
        current_time = datetime.datetime.now()
        if 'last-active' in online_clients[timeout_socket]:
            minus_timeout = current_time - datetime.timedelta(seconds=timeout)
            if minus_timeout == online_clients[timeout_socket]['last-active'] or minus_timeout > online_clients[timeout_socket]['last-active']:
                print('Connection timeout for: {} since {}'.format(online_clients[timeout_socket]['data'].decode().split(',')[0], (online_clients[timeout_socket]['last-active'] + datetime.timedelta(seconds=timeout)).strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]))
                user = 'WICKWICK\'S SERVER'.encode()
                user_header = f"{len(user):<{20}}".encode()
                message = 'Connection Timeout at {} due to inactivity. Bye {}!'.format((online_clients[timeout_socket]['last-active'] + datetime.timedelta(seconds=timeout)).strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3], online_clients[timeout_socket]['data'].decode().split(',')[0]).encode()
                message_header = f"{len(message):<{20}}".encode()
                timeout_socket.send(user_header + user + message_header + message)

                # add to logged out list
                offline_clients[timeout_socket] = online_clients[timeout_socket]

                # Remove from list for socket.socket()
                sockets_list.remove(timeout_socket)

                # Remove from our list of users
                del online_clients[timeout_socket]

                # send indication of termination to client
                timeout_socket.shutdown(SHUT_RDWR)
                timeout_socket.close()
    # --- timeout end ---

    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket and notified_socket not in online_clients:

            # Accept new connection
            client_socket, client_address = server_socket.accept()

            # to track retry count
            retry_count = 0

            # Client send message
            while(1):
                # FIXME if have time implement this extra feature
                # --- accept timeout start ---
                # 60 second to login else close connection, others waiting
                # current_time = datetime.datetime.now()
                
                # if current_time > (accepted_time + datetime.timedelta(seconds=60)):
                #     print(f'Connection timeout for: {client_address}')
                #     message = 'Connection Timeout, login faster!'.encode()
                #     message_header = f"{len(message):<{20}}".encode()
                #     timeout_socket.send(message_header + message)
                #     break
                # --- accept timeout end ---

                user = receive_message(client_socket)
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
                            print(f'UNBLOCKED: {username}\'s account!')
                            if username == credentials[0]:
                                message = 'Your account have been UNBLOCKED since {}, {}!'.format(current_time.strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3], username).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)
                                del blocked_clients[blocked]
                                break
                        elif minus_blocked < blocked_clients[blocked]['account-blocked']:
                            check = username
                            if username == credentials[0]:
                                print(f'BLOCKED: {username} is still blocked!')
                                message = 'Your account is blocked {}. Please try again after {}!'.format(username, (blocked_clients[blocked]['account-blocked'] + datetime.timedelta(seconds=block_duration)).strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                client_socket.send(message_header + message)
                                client_socket.shutdown(SHUT_RDWR)
                                client_socket.close()
                            break
                    continue
                # if user tries to login after block with new client_socket
                if check == credentials[0]:
                    break
                # --- block_duration end ---

                # --- Check duplicate login start ---
                if user_exists_On9clients(username=credentials[0], on9clients=online_clients):
                    print(f'AUTHENTICATION :{credentials[0]} is already online. FAILED!')
                    message = f'SERVER: {credentials[0]} is already online!'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)
                    break
                # --- Check duplicate login end ---

                # --- Authentication start ---
                result = authenticate(credential=credentials)

                print(f'AUTHENTICATION for {credentials[0]}: {result}')
                if 'Successful' in result:

                    # Add accepted socket to select() list
                    sockets_list.append(client_socket)

                    user['logged-in'] = datetime.datetime.now()

                    # to check user inactivity - timeout
                    user['last-active'] = user['logged-in']

                    # user will have user_header and credentials
                    online_clients[client_socket] = user

                    username = user['data'].decode().split(',')[0]
                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, username))
                    # client_socket.send(f'Welcome {username}'.encode())

                    message = '--------------------------'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = '---- offline messages ----'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    message = '--------------------------'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    # update logged out clients list and send all offline message(s)
                    for offline_socket in offline_clients:
                        if offline_clients[offline_socket]['data'].decode().split(',')[0] == credentials[0]:
                            if offline_socket in offline_messages:
                                for msg in offline_messages[offline_socket]:
                                    # print(offline_messages[msg])
                                    if credentials[0] == msg['recipient'].decode().split(',')[0]:
                                        message = '{} > {}'.format(msg['sender'].decode().split(',')[0], msg['message'].decode()).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        client_socket.send(message_header + message)
                                del offline_messages[offline_socket]
                            del offline_clients[offline_socket]
                            break

                    message = '--------------------------'.encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    # send login date time
                    message = 'Welcome back {}! You logged in at: {}'.format(username, user['logged-in'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    break
                else:
                    if 'Password' in result:
                        retry_count += 1
                        user['retry'] = retry_count
                        # if fail 3rd retry, block user
                        if user['retry'] >= 3:
                            print(f'BLOCKED: {credentials[0]}\'s account. Retry count :{retry_count}')
                            user['account-blocked'] = datetime.datetime.now()
                            message = 'Invalid Password. Retry count limit reached. Please try again later after {}. {}, Your account has been blocked!'.format((user['account-blocked'] + datetime.timedelta(seconds=block_duration)).strftime("%H:%M:%S.%f")[:-3], credentials[0]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            client_socket.send(message_header + message)
                            
                            # user will have username, user_header and block duration
                            user['data'] = credentials[0].encode()

                            # add user to block account list
                            blocked_clients[client_socket] = user

                            break
                        # Invalid password, prompt sender try again
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
        # After authentication successful, server start to send user and message (both with their headers)
        # server will reuse message header sent by sender for certain commands like message, broadcasting, etc
        elif notified_socket in online_clients and notified_socket not in blocked_clients:
        # else:
            
            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]))

                # add to offline user list
                if notified_socket not in offline_clients:
                    offline_clients[notified_socket] = online_clients[notified_socket]

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of online users
                del online_clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = online_clients[notified_socket]

            if user is False:
                continue

            user['last-active'] = datetime.datetime.now()

            print('Received message at {} from {}: {}'.format(user['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3], user["data"].decode().split(',')[0], message["data"].decode()))

            # --- Commands start ---
            command = message["data"].decode().split(' ')[0]
            # --- broadcast start ---
            if command == 'broadcast':
                check = message['data'].decode().split(' ')
                if len(check) >= 2:
                    message['data'] = message['data'].decode().split(' ', 1)[1].encode()
                    # Iterate over online user and broadcast message
                    exist = False
                    for client_socket in online_clients:
                        blocked = False
                        # But don't sent it to sender
                        if client_socket != notified_socket:
                            # check if user in my block list
                            if 'blocked-user' in online_clients[notified_socket]:
                                for i in range(len(online_clients[notified_socket]['blocked-user'])):
                                    if online_clients[client_socket]['data'] == online_clients[notified_socket]['blocked-user'][i]['data']:
                                        exist = True
                                        blocked = True
                                        break
                            # check if me in user block list
                            if 'blocked-user' in online_clients[client_socket]:
                                for i in range(len(online_clients[client_socket]['blocked-user'])):
                                    if online_clients[notified_socket]['data'] == online_clients[client_socket]['blocked-user'][i]['data']:
                                        exist = True
                                        blocked = True
                                        break
                            if blocked == False:
                                client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                    if exist:
                        print('{} some user will not get the broadcast!'.format(user['data'].decode().split(',')[0]))
                        message = 'some user will not get the broadcast, {}!'.format(user['data'].decode().split(',')[0]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        break
                else:
                    print('FAIL: No message to broadcast, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'No message to broadcast, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- broadcast end ---

            # --- whoelse start ---
            elif command == 'whoelse':
                check = message['data'].decode().split(' ')
                if len(check) == 1:
                    # checks online user list
                    for client_socket in online_clients:
                        if client_socket != notified_socket and client_socket not in blocked_clients:
                            message = '{} is online!'.format(online_clients[client_socket]['data'].decode().split(',')[0]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    print('FAIL: whoelse need no args, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'whoelse need no args, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- whoelse end ---

            # --- whoelsesince start ---
            elif command == 'whoelsesince':
                check = message['data'].decode().split(' ')
                if len(check) == 2:
                    # checks online user list
                    for client_socket in online_clients:
                        current_time = datetime.datetime.now()
                        sec = message['data'].decode()
                        sec = int(sec.split(' ')[1])
                        t = online_clients[client_socket]['logged-in'] + datetime.timedelta(seconds=sec)
                        # if not self and user is not blocked and user is not offline
                        if client_socket != notified_socket and client_socket not in blocked_clients and client_socket not in offline_clients:
                            # if user's logged in time + <seconds> more than or equals to current time diplay user
                            if t > current_time or t == current_time: 
                                msg = '{} IS online, last active: {}!'.format(online_clients[client_socket]['data'].decode().split(',')[0], online_clients[client_socket]['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                                message_header = f"{len(msg):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + msg)
                    # checks offline user list
                    for client_socket in offline_clients:
                        current_time = datetime.datetime.now()
                        sec = message['data'].decode()
                        sec = int(sec.split(' ')[1])
                        t = offline_clients[client_socket]['logged-in'] + datetime.timedelta(seconds=sec)
                        # if not self and user is not blocked and user is not online
                        if client_socket != notified_socket and client_socket not in blocked_clients and client_socket not in online_clients:
                            # if user's logged in time + <seconds> more than or equals to current time diplay user
                            if t > current_time or t == current_time:
                                msg = '{} WAS online, last active: {}!'.format(offline_clients[client_socket]['data'].decode().split(',')[0], offline_clients[client_socket]['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                                message_header = f"{len(msg):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + msg)
                else:
                    print('FAIL: Insufficient Args or Too Many Args, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args or Too Many Args, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- whoelsesince end ---

            # --- message start ---
            elif command == 'message':
                check = message['data'].decode().split(' ')
                if len(check) < 3:
                    print('FAIL: Insufficient Args, {}!'.format(online_clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args, {}!'.format(online_clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    # if self fail
                    if check[1] == user['data'].decode().split(',')[0]:
                        print('{} can\'t MESSAGE SELF!'.format(check[1]))
                        message = 'can\'t MESSAGE SELF: {}!'.format(check[1]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                    else:
                        recipient = message['data'].decode().split(' ')[1]
                        msg = message['data'].decode().split(' ', 2)[2]

                        if user_exists(username=recipient, on9clients=online_clients, off9clients=offline_clients):
                            # check if recipient is online
                            for client_socket in online_clients:
                                if client_socket != notified_socket and online_clients[client_socket]['data'].decode().split(',')[0] == recipient:
                                    # if send successful sender will NOT get notified
                                    if user_blocked(my_socket=notified_socket, on9clients=online_clients, off9clients=offline_clients):
                                        message = 'Error, can\'t send message to: {}! *{} blocked you...'.format(recipient, recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    else:
                                        print('on9 MESSAGE sent to {} from {}'.format(recipient, user['data'].decode().split(',')[0]))
                                        msg = msg.strip().encode()
                                        message_header = f"{len(msg):<{20}}".encode()
                                        client_socket.send(user['header'] + user['data'] + message_header + msg)
                            # check if recipient is offline
                            for client_socket in offline_clients:
                                if client_socket != notified_socket and offline_clients[client_socket]['data'].decode().split(',')[0] == recipient:
                                    # if send successful sender will get notified
                                    if not user_blocked(my_socket=notified_socket, on9clients=online_clients, off9clients=offline_clients):
                                        msg = msg.strip().encode()
                                        # message_header = f"{len(msg):<{20}}".encode()
                                        # client_socket.send(user['header'] + user['data'] + message_header + msg)
                                        if client_socket in offline_messages:
                                            offline_messages[client_socket].append({'sender_header': user['header'], 'sender': user['data'], 'recipient': offline_clients[client_socket]['data'], 'message':msg })
                                        else:
                                            offline_messages[client_socket] = [{'sender_header': user['header'], 'sender': user['data'], 'recipient': offline_clients[client_socket]['data'], 'message':msg }]
                                        print('off9 MESSAGE sent to {} from {}'.format(recipient, user['data'].decode().split(',')[0]))
                                        message = 'sent message to: {} successful!'.format(recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    else:
                                        print(f'off9 MESSAGE FAIL: can\'t send to {recipient}')
                                        message = 'Error, can\'t send offline message to: {}! *{} blocked you...'.format(recipient, recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        # if user in credentials.txt but never log in
                        # if user not in credentials.txt
                        else:
                            print('FAIL: {} doesn\'t exist!'.format(check[1]))
                            message = 'Error, {} doesn\'t exist!'.format(check[1]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- message end ---

            # --- block start ---
            elif command == 'block':
                check = message['data'].decode().split(' ')
                if len(check) == 2:
                    # if self fail
                    if check[1] == user['data'].decode().split(',')[0]:
                        print('{} can\'t BLOCK SELF!'.format(check[1]))
                        message = 'can\'t BLOCK SELF: {}!'.format(check[1]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                    # checks if user exist
                    elif user_exists(username=check[1], on9clients=online_clients, off9clients=offline_clients):
                        # checks my block list if user is online
                        for client_socket in online_clients:
                            if client_socket != notified_socket and online_clients[client_socket]['data'].decode().split(',')[0] == check[1]:
                                if 'blocked-user' not in online_clients[notified_socket]:
                                    online_clients[notified_socket]['blocked-user'] = [online_clients[client_socket]]
                                else:
                                    # check if user in my block list
                                    exist = False
                                    for i in range(len(online_clients[notified_socket]['blocked-user'])):
                                        if check[1] == online_clients[notified_socket]['blocked-user'][i]['data'].decode().split(',')[0]:
                                            print('{} already BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], check[1]))
                                            message = 'already BLOCKED USER: {}!'.format(check[1]).encode()
                                            message_header = f"{len(message):<{20}}".encode()
                                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                                            exist = True
                                            break
                                    if exist:
                                        break

                                    online_clients[notified_socket]['blocked-user'].append(online_clients[client_socket])
                                
                                print('{} BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], online_clients[client_socket]['data'].decode().split(',')[0]))
                                message = 'BLOCKED USER: {}!'.format(online_clients[client_socket]['data'].decode().split(',')[0]).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                break
                        # checks my block list if user is offline
                        for client_socket in offline_clients:
                            if client_socket != notified_socket and offline_clients[client_socket]['data'].decode().split(',')[0] == check[1]:
                                if 'blocked-user' not in online_clients[notified_socket]:
                                    online_clients[notified_socket]['blocked-user'] = [offline_clients[client_socket]]
                                else:
                                    exist = False
                                    for i in range(len(online_clients[notified_socket]['blocked-user'])):
                                        if check[1] == online_clients[notified_socket]['blocked-user'][i]['data'].decode().split(',')[0]:
                                            print('{} already BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], check[1]))
                                            message = 'already BLOCKED USER: {}!'.format(check[1]).encode()
                                            message_header = f"{len(message):<{20}}".encode()
                                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                                            exist = True
                                            break
                                    if exist:
                                        break
                                    online_clients[notified_socket]['blocked-user'].append(offline_clients[client_socket])
                                print('{} BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], offline_clients[client_socket]['data'].decode().split(',')[0]))
                                message = 'BLOCKED USER: {}!'.format(offline_clients[client_socket]['data'].decode().split(',')[0]).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                break
                    # if user in credentials.txt but never log in
                    # if user not in credentials.txt
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
                    # if self fail
                    if check[1] == user['data'].decode().split(',')[0]:
                        print('{} can\'t UNBLOCK SELF!'.format(check[1]))
                        message = 'can\'t UNBLOCK SELF: {}!'.format(check[1]).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        break

                    # checks my blocked user list
                    for client_socket in online_clients:
                        if 'blocked-user' in online_clients[notified_socket]:
                            # blocked-user is an array of dicts
                            for i in range(len(online_clients[notified_socket]['blocked-user'])):
                                if check[1] == online_clients[notified_socket]['blocked-user'][i]['data'].decode().split(',')[0]:
                                    print('{} UNBLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], check[1]))
                                    message = 'UNBLOCKED USER: {}!'.format(check[1]).encode()
                                    message_header = f"{len(message):<{20}}".encode()
                                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    del online_clients[notified_socket]['blocked-user'][i]
                                    break
                        else:
                            print('FAIL: to unblock: {}!'.format(check[1]))
                            message = 'Error, fail to unblock {}!'.format(check[1]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                            break
                else:
                    print('FAIL: Insufficient Args or Too Many Args: {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args or Too Many Args: {}!'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- unblock end ---

            # --- logout start ---
            elif command == 'logout':
                check = message['data'].decode().split(' ')
                if len(check) == 1:
                    current_time = datetime.datetime.now()

                    print('Connection close for: {} at {}'.format(user['data'].decode().split(',')[0], current_time.strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]))
                    message = 'Logged out at {} Bye!'.format(current_time.strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)

                    # add to logged out list
                    offline_clients[notified_socket] = online_clients[notified_socket]

                    # Remove from list for socket.socket()
                    sockets_list.remove(notified_socket)

                    # Remove from our list of users
                    del online_clients[notified_socket]

                    # send indication of termination to client
                    notified_socket.shutdown(SHUT_RDWR)
                    notified_socket.close()
                else:
                    print('FAIL: Too many Args: {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Too many Args: {}!'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- logout end ---

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

        # Remove from online list of users
        del online_clients[notified_socket]