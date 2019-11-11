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
				return f'{check[0]} --> Login Successful'
			if creds[0] == check[0] and creds[1] != check[0]:
				return 'Invalid Password. Please try again!'
			line = reader.readline()
		# return "Invalid Password"
		return 'Invalid Username. Please try again!'
