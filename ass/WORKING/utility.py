'''
# Python 3
# Author: z5147986
'''

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
