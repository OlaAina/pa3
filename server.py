from pickle import TRUE
import socket
import signal
import sys
import random
import hashTable

# Read a command line argument for the port where the server
# must run.
port = 8080
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)

### Contents of pages we will serve.
# Login form
login_form = """
   <form action = "http://localhost:%d" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
""" % port
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = """
   <h1>Welcome!</h1>
   <form action="http://localhost:%d" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
""" % port


#### Helper functions
# Printing.
def print_value(tag, value):
    print "Here is the", tag
    print "\"\"\""
    print value
    print "\"\"\""
    print


# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)


# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)

# TODO: put your application logic here!
# Read login credentials for all the users
# Read secret data of all the users
# CHECK 

user_pass = hashTable.hashTable(100)
user_secret = hashTable.hashTable(100)
user_cookie = hashTable.hashTable(100)


def buildUserPassDatabase():
    passwords = open("passwords.txt", "r")
    for line in passwords:
        data = line.split()
        user_pass.set_val(data[0], data[1])


def buildUserSecretDatabase():
    secrets = open("secrets.txt", "r")
    for line in secrets:
        data = line.split()
        user_secret.set_val(data[0], data[1])


buildUserPassDatabase()
buildUserSecretDatabase()


def parseEntity(body):
    data = bytes(body).split('&')

    if len(data) > 1:
        user = data[0]
        psw = data[1]

        user = user.split('=')[1]
        psw = psw.split('=')[1]
    else:
        data = bytes(body).split('=')
        if data[0] == 'username':
            user = data[1]
            psw = ''
        else:
            user = ''
            psw = data[1]

    return user, psw


def store_cookie(cookie, username):
    user_cookie.set_val(cookie, username)


# you have to parse the header and check if there
# the reason why the cookie is from the last run is the reason why you have case return 0. Makes sense cause it should
# persist after server is closed
def find_cookie(headers):
    data = headers.split('\r\n')
    for line in data:
        if "Cookie" in line:
            get_line = line.split("=")
            if user_cookie.get_val(get_line[1]):
                return 1
            else:
                return 0
    return 2


### Loop to accept incoming HTTP connections and respond.
while True:

    client, addr = sock.accept()
    req = client.recv(1024)

    # Let's pick the headers and entity body apart
    header_body = req.split('\r\n\r\n')
    headers = header_body[0]
    body = '' if len(header_body) == 1 else header_body[1]
    print_value('headers', headers)
    print_value('entity body', body)

    # if flag is 1 cookie is valid
    # if flag is 0 there is cookie but not valid
    # if flag is 2 there is no cookie at all so proceed to normal authentication
    headers_to_send = ''
    flag = find_cookie(headers)

    # TODO: Put your application logic here!
    # Parse headers and body and perform various actions

    # You need to set the variables:
    # (1) `html_content_to_send` => add the HTML content you'd
    # like to send to the client.
    # Right now, we just send the default login page.
    if flag == 1:
        data = headers.split('\r\n')
        for lines in data:
            if "Cookie" in lines:
                headings = lines.split("=")
                cookie = headings[1]
        user = user_cookie.get_val(cookie)
        secret = user_secret.get_val(user)
        html_content_to_send = success_page + secret + '\n'
        headers_to_send = ''

    if flag == 2:
        html_content_to_send = login_page

        if body:
            user, psw = parseEntity(body)
            if (user_pass.get_val(user) != '' or user != '') and user_pass.get_val(user) == psw:
                html_content_to_send = success_page + user_secret.get_val(user) + '\n'
                rand_val = random.getrandbits(64)
                headers_to_send = 'Set-Cookie: token=' + str(rand_val) + '\r\n'
                store_cookie(str(rand_val), user)
            else:
                html_content_to_send = bad_creds_page
                headers_to_send = ''
    if flag == 0:
        html_content_to_send = bad_creds_page
        headers_to_send = ''
    # But other possibilities exist, including
    # html_content_to_send = success_page + <secret>
    # html_content_to_send = bad_creds_page
    # html_content_to_send = logout_page

    # (2) `headers_to_send` => add any additional headers
    # you'd like to send the client?
    # Right now, we don't send any extra headers.

    #headers_to_send = ''

    # Construct and send the final response
    response = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response)
    client.send(response)
    client.close()

    print "Served one request/connection!"
    print

# We will never actually get here.
# Close the listening socket
sock.close()
