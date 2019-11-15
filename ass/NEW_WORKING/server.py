'''
Used the sample code as reference from 
https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
Coding: utf-8
Author: z5147986, wickwickthedog
Usage: 
(default) - pyhton3 server.py <port> <block duration> <timeout>
'''

from socket import *
from select import *
from utility import receive_message, authenticate, user_exists_On9clients, user_exists_Off9clients, user_exists, user_blocked_list, user_blocked,length_encoded_msg
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

# List of offline messages
offline_messages = {}

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

                    print('Accepted new connection from {}:{} ~> {}'.format(*client_address, user['data'].decode()))

                    # send login date time
                    message = 'Welcome back {}! You Logged in at: {}'.format(user['data'].decode(), user['logged-in'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    client_socket.send(message_header + message)

                    # update logged out clients list and send all offline message(s)
                    for offline_socket in offline_clients:
                        if offline_clients[offline_socket]['data'].decode() == user['data'].decode():
                            if offline_socket in offline_messages:
                                for msg in offline_messages[offline_socket]:
                                    # print(offline_messages[msg])
                                    if user['data'].decode() == msg['recipient'].decode():
                                        message = '{} > {}'.format(msg['sender'].decode(), msg['message'].decode()).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        client_socket.send(message_header + message)
                                del offline_messages[offline_socket]
                            del offline_clients[offline_socket]
                            break
                    
                    message = 'offline messages successful, {}'.format(user['data'].decode()).encode()
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

            # retrive user from list of online clients
            user = online_clients[notified_socket]

            if user is False:
                continue

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
                notified_socket.send(server_header + server + message_header + message)

                # add to offline list
                offline_clients[notified_socket] = user

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del online_clients[notified_socket]
                continue
            # --- timeout end ---

            # update user's last active
            user['last-active'] = datetime.datetime.now()

            print('Received message at {} from {}: {}'.format(user['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3], user["data"].decode(), message["data"].decode()))

            # --- Commands start ---
            command = message["data"].decode().strip().split(' ')[0]
            # --- empty ---
            if command == '':
                #FIXME uncomment debugging print before submitting
                print('No command specified, {}!'.format(user['data'].decode()))
                message = 'No command specified, {}!'.format(user['data'].decode()).encode()
                message_header = f"{len(message):<{20}}".encode()
                notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- empty ---

            # --- broadcast start ---
            elif command == 'broadcast':
                if length_encoded_msg(encoded_msg=message['data']) >= 2:
                    # remove command from message
                    message['data'] = message['data'].decode().split(' ',1)[1].encode()
                    # update message header
                    message['header'] = f"{len(message['data']):<{20}}".encode()
                    for client_socket in online_clients:
                        if client_socket != notified_socket:
                            if 'blocked-user' in user:
                                # check if user in my block list
                                if user_blocked_list(my_socket=notified_socket, to_check_socket=client_socket, on9clients=online_clients):
                                    continue
                            if 'blocked-user' in online_clients[client_socket]:
                                # check if me in user block list
                                if user_blocked_list(my_socket=client_socket, to_check_socket=notified_socket, on9clients=online_clients):
                                     continue
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                    # successful
                    message = 'broadcast successful, {}!'.format(user['data'].decode()).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    #FIXME uncomment debugging print before submitting
                    # print('FAIL: No message to broadcast, {}'.format(user['data'].decode()))
                    message = 'Error, No message to broadcast, {}'.format(user['data'].decode()).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- broadcast end ---

            # --- whoelse start ---
            elif command == 'whoelse':
                if length_encoded_msg(encoded_msg=message['data']) == 1:
                    # total online clients minus self = 0 means I am the only one
                    if (len(list(online_clients)) - 1) == 0:
                        # since whoelse doesn't siplay self
                        message = 'whoelse successful, {}!'.format(user['data'].decode()).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        break
                    # send client the number of online client
                    #FIXME uncomment debugging print before submitting
                    # print('whoelse {}'.format(len(list(online_clients)) - 1))
                    message = 'whoelse {}'.format(len(list(online_clients)) - 1).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                    # checks online user list
                    for client_socket in online_clients:
                        if client_socket != notified_socket:

                            # print('{} is online!'.format(online_clients[client_socket]['data'].decode()))
                            message = '{} is online!'.format(online_clients[client_socket]['data'].decode()).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                    # successful
                    message = 'whoelse successful, {}!'.format(user['data'].decode()).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    #FIXME uncomment debugging print before submitting
                    # print('FAIL: whoelse need no args, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'Error, whoelse need no args, {}'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- whoelse end ---

            # --- whoelsesince start ---
            elif command == 'whoelsesince':
                if length_encoded_msg(encoded_msg=message['data']) == 2:
                    # total online clients minus self = 0 means I am the only one
                    if (len(list(online_clients)) - 1) == 0 and len(list(offline_clients)) == 0:
                        message = 'whoelsesince successful, {}!'.format(user['data'].decode()).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        break
                    # checks online user list
                    for client_socket in online_clients:
                        current_time = datetime.datetime.now()
                        # sec = message['data'].decode()
                        # sec = int(sec.split(' ')[1])
                        sec = int(message['data'].decode().split(' ')[1])
                        logged_in_time = online_clients[client_socket]['logged-in'] + datetime.timedelta(seconds=sec)
                        # if not self and user not offline
                        if client_socket != notified_socket and client_socket not in offline_clients:
                            # if user's logged in time + <seconds> more than or equals to current time diplay user
                            if logged_in_time > current_time or logged_in_time == current_time: 
                                msg = '{} IS online, last active: {}!'.format(online_clients[client_socket]['data'].decode(), online_clients[client_socket]['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                                message_header = f"{len(msg):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + msg)
                    # checks offline user list
                    for client_socket in offline_clients:
                        current_time = datetime.datetime.now()
                        # sec = message['data'].decode()
                        # sec = int(sec.split(' ')[1])
                        sec = int(message['data'].decode().split(' ')[1])
                        logged_in_time = offline_clients[client_socket]['logged-in'] + datetime.timedelta(seconds=sec)
                        # if not self and user is not online
                        if client_socket != notified_socket and client_socket not in blocked_clients and client_socket not in online_clients:
                            # if user's logged in time + <seconds> more than or equals to current time diplay user
                            if logged_in_time > current_time or logged_in_time == current_time:
                                msg = '{} WAS online, last active: {}!'.format(offline_clients[client_socket]['data'].decode(), offline_clients[client_socket]['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                                message_header = f"{len(msg):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + msg)
                    # successful
                    message = 'whoelsesince successful, {}!'.format(user['data'].decode()).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    #FIXME uncomment debugging print before submitting
                    # print('FAIL: Insufficient Args or Too Many Args, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args or Too Many Args, {}'.format(online_clients[notified_socket]['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- whoelsesince end ---

            # --- message start ---
            elif command == 'message':
                if length_encoded_msg(encoded_msg=message['data']) < 3:
                    #FIXME uncomment debugging print before submitting
                    # print('FAIL: Insufficient Args, {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args, {}!'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    recipient = message['data'].decode().split(' ')[1]
                    # if self fail
                    if recipient == user['data'].decode().split(',')[0]:
                        #FIXME uncomment debugging print before submitting
                        # print('FAIL: {} can\'t MESSAGE SELF!'.format(recipient))
                        message = 'Error, can\'t message self: {}!'.format(recipient).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                    else:
                        msg = message['data'].decode().split(' ', 2)[2]

                        if user_exists(username=recipient, on9clients=online_clients, off9clients=offline_clients):
                            # check if recipient is online
                            for client_socket in online_clients:
                                if client_socket != notified_socket and online_clients[client_socket]['data'].decode() == recipient:
                                    # if send successful sender will NOT get notified
                                    if user_blocked(my_socket=notified_socket, on9clients=online_clients, off9clients=offline_clients):
                                        message = 'Error, can\'t send message to: {}! *{} blocked you...'.format(recipient, recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    else:
                                        #FIXME uncomment debugging print before submitting
                                        # print('on9 MESSAGE sent to {} from {}'.format(recipient, user['data'].decode().split(',')[0]))
                                        msg = msg.strip().encode()
                                        message_header = f"{len(msg):<{20}}".encode()
                                        client_socket.send(user['header'] + user['data'] + message_header + msg)
                                        # successful
                                        message = 'online message successful, {}!'.format(user['data'].decode()).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)

                            # check if recipient is offline
                            for client_socket in offline_clients:
                                if client_socket != notified_socket and offline_clients[client_socket]['data'].decode() == recipient:
                                    # if send successful sender will get notified
                                    if not user_blocked(my_socket=notified_socket, on9clients=online_clients, off9clients=offline_clients):
                                        msg = msg.strip().encode()
                                        # message_header = f"{len(msg):<{20}}".encode()
                                        # client_socket.send(user['header'] + user['data'] + message_header + msg)
                                        if client_socket in offline_messages:
                                            offline_messages[client_socket].append({'sender_header': user['header'], 'sender': user['data'], 'recipient': offline_clients[client_socket]['data'], 'message':msg })
                                        else:
                                            offline_messages[client_socket] = [{'sender_header': user['header'], 'sender': user['data'], 'recipient': offline_clients[client_socket]['data'], 'message':msg }]
                                        #FIXME uncomment debugging print before submitting
                                        # print('off9 MESSAGE sent to {} from {}'.format(recipient, user['data'].decode().split(',')[0]))
                                        message = 'sent offline message to: {} successful!'.format(recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                        # successful
                                        message = 'offline message successful, {}!'.format(user['data'].decode()).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    else:
                                        #FIXME uncomment debugging print before submitting
                                        # print(f'off9 MESSAGE FAIL: can\'t send to {recipient}')
                                        message = 'Error, can\'t send offline message to: {}! *{} blocked you...'.format(recipient, recipient).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        # if user in credentials.txt but never log in
                        # if user not in credentials.txt
                        else:
                            #FIXME uncomment debugging print before submitting
                            # print('FAIL: {} doesn\'t exist!'.format(recipient))
                            message = 'Error, {} doesn\'t exist!'.format(recipient).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- message end ---

            # --- block start ---
            elif command == 'block':
                if length_encoded_msg(encoded_msg=message['data']) == 2:
                    username = message['data'].decode().split(' ')[1]
                    # if self fail
                    if username == user['data'].decode():
                        #FIXME uncomment debugging print before submitting
                        # print('{} can\'t BLOCK SELF!'.format(username))
                        message = 'Error, can\'t block self: {}!'.format(username).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                    # checks if user exist
                    elif user_exists(username=username, on9clients=online_clients, off9clients=offline_clients):
                        # checks my block list if user is online
                        for client_socket in online_clients:
                            if client_socket != notified_socket and online_clients[client_socket]['data'].decode() == username:
                                if 'blocked-user' not in user:
                                    # create new key for an array of blocked clients
                                    user['blocked-user'] = [online_clients[client_socket]]
                                else:
                                    # check if user in my block list
                                    if user_blocked_list(my_socket=notified_socket, to_check_socket=client_socket, on9clients=online_clients):
                                        message = 'Error, already blocked {}!'.format(username).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                        break
                                    # add to my block list
                                    user['blocked-user'].append(online_clients[client_socket])

                                # print('{} BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], online_clients[client_socket]['data'].decode().split(',')[0]))
                                message = 'blocked {}!'.format(username).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                # successful
                                message = 'block successful, {}!'.format(user['data'].decode()).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                break
                        # checks my block list if user is offline
                        for client_socket in offline_clients:
                            if client_socket != notified_socket and offline_clients[client_socket]['data'].decode() == username:
                                if 'blocked-user' not in user:
                                    user['blocked-user'] = [offline_clients[client_socket]]
                                else:
                                    if user_blocked_list(my_socket=notified_socket, to_check_socket=client_socket, on9clients=online_clients):
                                        message = 'Error, already blocked {}!'.format(username).encode()
                                        message_header = f"{len(message):<{20}}".encode()
                                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                                        break
                                    # add to my block list
                                    user['blocked-user'].append(offline_clients[client_socket])
                                # print('{} BLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], offline_clients[client_socket]['data'].decode().split(',')[0]))
                                message = 'blocked {}!'.format(username).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                # successful
                                message = 'block successful, {}!'.format(user['data'].decode()).encode()
                                message_header = f"{len(message):<{20}}".encode()
                                notified_socket.send(user['header'] + user['data'] + message_header + message)
                                break
                    # if user in credentials.txt but never log in
                    # if user not in credentials.txt
                    else:
                        #FIXME uncomment debugging print before submitting
                        # print('FAIL: {} doesn\'t exist!'.format(username))
                        message = 'Error, {} doesn\'t exist!'.format(username).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    #FIXME uncomment debugging print before submitting
                    # print('FAIL: Insufficient Args: {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args: {}!'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- block end ---

            # --- unblock start ---
            elif command == 'unblock':
                if length_encoded_msg(encoded_msg=message['data']) == 2:
                    username = message['data'].decode().split(' ')[1]
                    # if self fail
                    if username == user['data'].decode():
                        #FIXME uncomment debugging print before submitting
                        # print('{} can\'t UNBLOCK SELF!'.format(username))
                        message = 'Error, can\'t unblock self: {}!'.format(username).encode()
                        message_header = f"{len(message):<{20}}".encode()
                        notified_socket.send(user['header'] + user['data'] + message_header + message)
                        break

                    # checks my blocked user list
                    for client_socket in online_clients:
                        if 'blocked-user' in user:
                            # blocked-user is an array of dicts
                            for i in range(len(user['blocked-user'])):
                                if username == user['blocked-user'][i]['data'].decode():
                                    # print('{} UNBLOCKED USER: {}!'.format(user['data'].decode().split(',')[0], username))
                                    message = 'unblocked {}!'.format(username).encode()
                                    message_header = f"{len(message):<{20}}".encode()
                                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    del user['blocked-user'][i]
                                    # successful
                                    message = 'unblock successful, {}!'.format(user['data'].decode()).encode()
                                    message_header = f"{len(message):<{20}}".encode()
                                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                                    break

                            #FIXME uncomment debugging print before submitting
                            # print('FAIL: to unblock: {}!'.format(username))
                            message = 'Error, fail to unblock {}!'.format(username).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            notified_socket.send(user['header'] + user['data'] + message_header + message)
                            break
                else:
                    #FIXME uncomment debugging print before submitting
                    # print('FAIL: Insufficient Args or Too Many Args: {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Insufficient Args or Too Many Args: {}!'.format(user['data'].decode()).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- unblock end ---

            # --- logout start ---
            elif command == 'logout':
                if length_encoded_msg(encoded_msg=message['data']) == 1:
                    current_time = datetime.datetime.now()
                    user['last-active'] = current_time

                    print('\nConnection close for: {} at {}\n'.format(user['data'].decode(), current_time.strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]))
                    message = 'Logged out successful at {} Bye!'.format(current_time.strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)

                    # broadcast log out message
                    for client_socket in online_clients:
                        blocked = False
                        # But don't sent it to sender
                        if client_socket != notified_socket:
                            if 'blocked-user' in user:
                                # check if user in my block list
                                if user_blocked_list(my_socket=notified_socket, to_check_socket=client_socket, on9clients=online_clients):
                                    continue
                            if 'blocked-user' in online_clients[client_socket]:
                                # check if me in user block list
                                if user_blocked_list(my_socket=client_socket, to_check_socket=notified_socket, on9clients=online_clients):
                                     continue
                            message = '{} Logged out at {}'.format(user['data'].decode(), user['last-active'].strftime("%d/%m/%Y, %H:%M:%S.%f")[:-3]).encode()
                            message_header = f"{len(message):<{20}}".encode()
                            client_socket.send(user['header'] + user['data'] + message_header + message)

                    # add to logged out list
                    offline_clients[notified_socket] = user

                    # Remove from list for socket.socket()
                    sockets_list.remove(notified_socket)
                    # Remove from our list of users
                    del online_clients[notified_socket]

                    #FIXME uncomment debugging print before submitting
                    # print(f'Number of Off9 clients: {len(list(offline_clients))}')
                    # successful
                    message = 'logout successful, {}!'.format(user['data'].decode()).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
                else:
                    #FIXME uncomment debugging print before submitting
                    # print('FAIL: Too many Args: {}!'.format(user['data'].decode().split(',')[0]))
                    message = 'Error, Too many Args: {}!'.format(user['data'].decode().split(',')[0]).encode()
                    message_header = f"{len(message):<{20}}".encode()
                    notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- logout end ---

            # --- P2P commands start---
            # elif command == 'startprivate':
            # P2P in that elif notified_socket in online_clients
            # if len(clients) == 2:
            #     print("Two clients have connected. Exchanging details for P2P")
            #     clients[0].send(tupleToDelimString(clients[1].getpeername()).encode())
            #     clients[1].send(tupleToDelimString(clients[0].getpeername()).encode())
            
            # --- default ---
            else:
                #FIXME uncomment debugging print before submitting
                # print('FAIL: Invalid Command, {}!'.format(user['data'].decode()))
                message = 'Error, Invalid Command, {}!'.format(user['data'].decode()).encode()
                message_header = f"{len(message):<{20}}".encode()
                notified_socket.send(user['header'] + user['data'] + message_header + message)
            # --- Commands end ---
    time.sleep(.25)

print("Server connection closed!")
sys.exit()