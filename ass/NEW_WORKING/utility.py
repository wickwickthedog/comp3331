'''
# Python 3
# Author: z5147986
'''

# helper function for both server and client to format receiving message 
# Handles message receiving and returns a dict
def receive_message(client_socket):
    try:
        # Receive header containing message length, it's size is defined as 20
        message_header = client_socket.recv(20)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(SHUT_RDWR)
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

# ----------Server helper function----------
# checks credentials
def authenticate(credential):
    if len(credential) < 2 or len(credential) > 2:
        return 'Invalid Username. Please try again!'
    credentials = 'credentials.txt'
    with open(credentials, 'r') as reader:
        line = reader.readline()
        while line != '': # EOF
            check = line.split()
            # print(check[0]) # username
            # print(check[1]) # password
            if credential == check:
                # login
                return 'Login Successful'
            if credential[0] == check[0] and credential[1] != check[0]:
                return 'Invalid Password. Please try again!'
            line = reader.readline()
        return 'Invalid Username. Please try again!'

# if user exist in online clients list
def user_exists_On9clients(username, on9clients):
    if username is '' or username is None or len(list(on9clients)) == 0:
        return False
    for sockets in on9clients:
        if username in on9clients[sockets]['data'].decode():
            return True
    return False

# if user exist in offline clients list
def user_exists_Off9clients(username, off9clients):
    if username is '' or username is None or len(list(off9clients)) == 0:
        return False
    for sockets in off9clients:
            if username in off9clients[sockets]['data'].decode():
                return True
    return False
    
# if user exist in online or offline clients list
def user_exists(username, on9clients, off9clients):
    if user_exists_On9clients(username, on9clients) or user_exists_Off9clients(username, off9clients):
        return True
    return False

# if user in my block list
# blocked-user is an array of dicts
def user_blocked_list(my_socket, to_check_socket, on9clients):
    if my_socket is None or to_check_socket is None or len(list(on9clients)) == 0:
        return False
    for blocked in on9clients[my_socket]['blocked-user']:
        if blocked['data'] == on9clients[to_check_socket]['data']:
            return True
    return False

# if user block or is blocked by someone
def user_blocked_On9clients(my_socket, on9clients):
    if my_socket is None or len(list(on9clients)) == 0:
        return False
    for client_socket in on9clients:
        if 'blocked-user' in on9clients[my_socket]:
            for blocked in on9clients[my_socket]['blocked-user']:
                if blocked['data'] == on9clients[client_socket]['data']:
                    return True
        if 'blocked-user' in on9clients[client_socket]:
            for blocked in on9clients[client_socket]['blocked-user']:
                if blocked['data'] == on9clients[my_socket]['data']:
                    return True
    return False

# if user is blocked by someone who is offline
def user_blocked_Off9clients(my_socket, off9clients, on9clients):
    if my_socket is None or len(list(on9clients)) == 0 or len(list(off9clients)) == 0:
        return False
    for client_socket in off9clients:
        if 'blocked-user' in off9clients[client_socket]:
            for blocked in off9clients[client_socket]['blocked-user']:
                if blocked['data'] == on9clients[my_socket]['data']:
                    return True
    return False

# if user block or is blocked by someone online or offline
def user_blocked(my_socket, on9clients, off9clients):
    if user_blocked_On9clients(my_socket, on9clients) or user_blocked_Off9clients(my_socket, off9clients, on9clients):
        return True
    return False

# return len of encoded message after split()
def length_encoded_msg(encoded_msg):
	return len(encoded_msg.decode().split(' '))