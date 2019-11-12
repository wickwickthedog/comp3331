'''
# Python 3
# Author: z5147986
'''

def authenticate(creds):
    credentials = 'credentials.txt'
    with open(credentials, 'r') as reader:
        line = reader.readline()
        while line != '': # EOF
            check = line.split()
            # print(check[0]) # username
            # print(check[1]) # password
            if creds == check:
                # login
                return 'Login Successful'
            if creds[0] == check[0] and creds[1] != check[0]:
                return 'Invalid Password. Please try again!'
            line = reader.readline()
        # return "Invalid Password"
        return 'Invalid Username. Please try again!'

def user_exists(username, clients, logged_out_clients):
    for sockets in clients:
        if username in clients[sockets]['data'].decode():
            return True
    for sockets in logged_out_clients:
        if username in logged_out_clients[sockets]['data'].decode():
            return True
    return False