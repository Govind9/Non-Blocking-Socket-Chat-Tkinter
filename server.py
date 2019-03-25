#Name: Karanjeet Singh
#UID: 1001703147
#LoginId:Kxs3147


import socket
import select
from _thread import *
import sys
from http import *
from tkinter import *
from threading import Thread
import json
import os

"""
the first argument AF_INET is the address domain of the socket. This is used when we have an Internet Domain
with any two hosts
The second argument is the type of socket. SOCK_STREAM means that data or characters are read in a continuous flow
"""
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)

#The server constants
IP = '127.0.0.1'
PORT = 8081
MAX_CONNS = 3

#The main GUI container
window = Tk()

#variables to hold clients data
clients = {i: None for i in range(1, MAX_CONNS + 1)}
usernames = {i: "Anonynmous_{}".format(i) for i in range(1, MAX_CONNS + 1)}

#variables to manage server status
online = False

def start_server():
    global online
    try:
        #initiate the server, adjust widgets status
        start_button.configure(state = DISABLED)
        while True:
            try:
                server.bind((IP, PORT)) 
                break
            except BlockingIOError as e:
                continue
        server.listen(100)
        online = True
        stop_button.configure(state = NORMAL)

        #start a new thread to handle incoming connections
        start_new_thread(accept_connections, ())
    except Exception as e:
        raise(e)
    return True
    
def stop_server():
    global online
    try:
        #notify each active client that server is closing
        msg = get_http_res('server', 406, "Server closing")
        for i in clients:
            if clients[i]:
                send_wait(clients[i], msg)
        
        #stop the server
        online = False
        server.close()
        window.destroy()
        sys.exit()
    except Exception as e:
        window.destroy()
        sys.exit()
        raise(e)
    return True
    
def accept_connections():
    global online
    global clients
    while online:
        try:
            """
            Accepts a connection request and stores two parameters, 
            conn which is a socket object for that user, and addr 
            which containsthe IP address of the client that just connected
            """
            conn_found = False
            conn, addr = server.accept()
            for i in clients:
                if clients[i] is None:
                    clients[i] = conn
                    online_label.configure(text = str(count_online()))
                    events.insert("end", 'User logged in.\n')
                    events.insert("end", '#'*15+'\n')
                    
                    #start a new thread to handle the client
                    start_new_thread(client_thread, (i, ))
                    conn_found = True
                    break
            if (not conn_found) and (conn):
                msg = get_http_res('server', 405, "Can't Connect Server Maxed")
                send_wait(conn, msg)
                conn.close()
        except BlockingIOError as e:
            continue
        except Exception as e:
            raise(e)

def client_thread(index):
    global online
    global usernames
    client = clients[index]
    
    #sends a welcome message to the client at index
    msg = get_http_res('server', 202, 'Welcome to this chatroom! UID: {}'.format(index))
    
    send_wait(client, msg)
    
    #client thread continues to listen to messages
    while online:
        try:     
            message = client.recv(2048).decode('utf-8')

            #parse the message                
            msg = parse_http_string(message)
            
            #decide course of action based on message type and purpose:
            if msg['type'] == 'GET':
                #do nothing here because polling is irrelevant in a real time delivery setup.
                events.insert("end", 'Received from {}:\n{}\n'.format(usernames[index], message))
                events.insert("end", '#'*15+'\n')
            elif msg['body'].startswith('uname- '):
                #message contains username for the client
                uname = msg['body'].split('uname- ')[1]
                if uname:
                    usernames[index] = uname
            elif msg['body'] == 'SEND USER LIST':
                #user asking for list of active users from the server
                user_list = {}
                for i in clients:
                    if clients[i]:
                        user_list[i] = usernames[i]
                user_list_msg = get_http_res('server', 201, json.dumps(user_list))
                send_wait(client, user_list_msg)
            elif msg['recv'] == 0:
                #This message is meant to be broadcasted
                events.insert("end", 'Received from {}:\n{}\n'.format(usernames[index], message))
                events.insert("end", '#'*15+'\n')
                sent = broadcast(index, msg['body'], msg['event_counter'])
                if not sent:
                    #send failure response to the client
                    err = get_http_res('server', 404, 'Client Offline')
                    send_wait(client, err)
            elif msg['recv'] > 0:
                #This message is meant for a particular user
                events.insert("end", 'Received from {}:\n{}\n'.format(usernames[index], message))
                events.insert("end", '#'*15+'\n')
                sent = send_to(index, msg['recv'], msg['body'], msg['event_counter'])
                if not sent:
                    #send failure response to the client
                    err = get_http_res('server', 404, 'Client Offline')
                    send_wait(client, err)
            elif msg['body'] == 'QUIT':
                #client asking for connection closure
                events.insert("end", 'Received from {}:\n{}\n'.format(usernames[index], message))
                events.insert("end", '#'*15+'\n')
                events.insert("end", '{} logging off.\n'.format(usernames[index]))
                events.insert("end", '#'*15+'\n')
                close_client(index)
                break
        except BlockingIOError as e:
            continue
        except Exception as e:
            raise(e)
            
def send_wait(client, msg):
    while online:
        try:
            client.send(msg.encode('utf-8'))
            break
        except BlockingIOError as e:
            continue
        except Exception as e:
            return
            
def send_to(from_index, to_index, message, counter):
    message = message
    msg = get_http_res(usernames[from_index], 200, message, '1', counter)
    if from_index == to_index:
        return False
    if not clients[to_index]:
        return False
    client = clients[to_index]
    try:
        send_wait(client, msg)
        events.insert("end", 'Send from {} to {}\n'.format(usernames[from_index], usernames[to_index]))
        events.insert("end", '#'*15+'\n')
        return True
    except Exception as e:
        client.close()
        close_client(to_index)
        return False

def broadcast(from_index, message, counter):
    message = message
    msg = get_http_res(usernames[from_index], 200, message, 'B', counter)
    for i in clients:
        if i == from_index or clients[i] == None:
            continue
        try:
            send_wait(clients[i], msg)
            events.insert("end", 'Broadcasted from {}\n'.format(usernames[from_index]))
            events.insert("end", '#'*15+'\n')
        except:
            clients[i].close()
            close_client(i)
    return True

def close_client(index):
    global clients
    global usernames
    try:
        if index in clients and clients[index]:
            #do some other stuff to close the things.
            usernames[index] = 'Anonymous_' + str(index)
            clients[index].close()
            clients[index] = None
            
            #Show the updated online counter
            online_label.configure(text = str(count_online()))
    except Exception as e:
        print(str(e))
        
def count_online():
    online_count = 0
    for i in clients:
        if clients[i]: 
            online_count += 1
    return online_count
    
#Widgets to show host IP address
Label(window, text="Server IP:").grid(row=0, column=0)
Label(window, text='localhost').grid(row=0, column=1)
#Widget to show host port number
Label(window, text="Port Number:").grid(row=0, column=2)
Label(window, text='8081').grid(row=0, column=3)
#Widget to show the number of online users
Label(window, text="Online:").grid(row=0, column= 4)
online_label = Label(window, text=str(count_online()))
online_label.grid(row=0, column=5)

#Widget to start server
start_button = Button(window, text = 'start', command = start_server)
start_button.grid(row = 1, column = 1, columnspan = 2)

#Widget for stop server
stop_button = Button(window, text = 'stop', state = DISABLED, command = stop_server)
stop_button.grid(row = 1, column = 3, columnspan = 2)

#Widget for the event log
events = Text(window)
events.grid(row=2, column=0, columnspan=6)

window.protocol('WM_DELETE_WINDOW', stop_server)
window.mainloop()
