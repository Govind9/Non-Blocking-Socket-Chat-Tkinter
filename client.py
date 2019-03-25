import socket
import sys
from http import *
from tkinter import *
from threading import Thread
from _thread import *
import json
import time
import os
import random
from lamport_clock import *

#server variable
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IP = 'localhost'
PORT = 8081

#Container for GUI
window = Tk()

#variable to track client online status and other information
online = False
USERNAME = ''
UID = -1
user_list = {}

#logical clock counter
counter = random.randint(0, 50)
counter_free = True
    
def start_chat():
    global online
    global server
    try:
        login_button.config(state = DISABLED)
        username_field.config(state = DISABLED)
        logout_button.config(state = NORMAL)
        broadcast_button.config(state = NORMAL)
        input_field.config(state = NORMAL)
        clock_label.configure(text = str(counter))
        
        
        server.setblocking(True)
        server.connect((IP, int(PORT)))
        server.setblocking(False)
        
        online = True
        #allow user to type in msgs now
        input_field.config(state = NORMAL)
        
        start_new_thread(recv_msg, ())
        
        #simulate sending and receiving and adjustment to clocks
        start_new_thread(internal_event_every_second, ())
        start_new_thread(sending_randomly, ())
    except Exception as e:
        raise(e)
        messages.insert("end", str(e), "left")
        end_chat()
        return False
    return True
    
def end_chat(self_end = False):
    global online
    try:
        if self_end:
            #send logout msg to server
            msg = get_http_req_post(-1, counter + 1, "QUIT")
            send_wait(server, msg)
        online = False
        server.close()
        login_button.config(state = NORMAL)
        logout_button.config(state = DISABLED)
        broadcast_button.config(state = DISABLED)
        input_field.config(state = DISABLED)
        window.destroy()
        sys.exit()
    except Exception as e:
        window.destroy()
        sys.exit()
    return True

def send_wait(client, msg, change_counter = False):
    global counter
    global counter_free
    
    if change_counter:
        #adjust logical clock counter
        while not counter_free: pass
        counter_free = False
        counter = send_event_adjustment(counter)
        counter_free = True
        clock_label.configure(text = str(counter))
    while True:
        try:
            client.send(msg.encode('utf-8'))
            break
        except BlockingIOError as e:
            continue
        except Exception as e:
            raise(e)
            return
    
def send_msg(event, mode, recv = 0, body = ''):
    try:
        cm = ''
        if mode == 'BROADCAST':
            cm = ''
        if mode == '121':
            if recv:
                #this came from random sending thread
                cm = ',{}'.format(user_list[recv])
            else:
                #this came from select bar
                x = om_variable.get()
                cm = ',{}'.format(x)
                for i in user_list:
                    if user_list[i] == x:
                        recv = i
                        break
        if not body:
            body = input_field.get()
        if body.strip() == '':
            return "break"
        text_msg.set('')
        msg = get_http_req_post(recv, counter + 1, body)
        send_wait(server, msg, True)
        messages.insert("end", 'Me({}{};{}): {}\n'.format(
                                                        mode[0],
                                                        cm,
                                                        counter,
                                                        body
                                                ), "right")
    except Exception as e:
        print(str(e))
        raise(e)
    return "break"
    
def recv_msg():
    global online
    global user_list
    global USERNAME
    global UID
    global counter
    global counter_free
    while online:
        try:
            message = server.recv(2048).decode('utf-8')
            
            #parse the http message
            msg = parse_http_string(message)
            
            #decide course of action based on message type and purpose:
            if msg['status'] == 200:
                #this is a normal message passed on by the server from another client
                
                #adjust logical clock counter
                while not counter_free: pass
                adjustment_needed = (recv_event_adjustment(counter, msg['event_counter']) > counter + 1)
                counter_free = False
                counter = recv_event_adjustment(counter, msg['event_counter'])
                counter_free = True
                clock_label.configure(text = str(counter))
                
                sender = msg['from'].split(' - ')[0]
                mode = msg['from'].split(' - ')[1]
                messages.insert("end", '{}({};{},{}{}): {}\n'.format(
                                                                    sender, 
                                                                    mode, 
                                                                    msg['event_counter'], 
                                                                    counter,
                                                                    "*" if adjustment_needed else "",
                                                                    msg['body']
                                                                ), "left")
                messages.insert("end", 'Sender Local Time: {}\n'.format(msg['event_counter']), "left")
                messages.insert("end", 'Clock Adjustment Needed: {}\n'.format("Yes" if adjustment_needed else "No"), "left")
                if adjustment_needed:
                    messages.insert("end", 'Time After Adjustment: {}\n'.format(counter), "left")
                else:
                    messages.insert("end", 'No Adjustment Needed, Current Time: {}\n'.format(counter), "left")
            elif msg['status'] == 201:
                #this message contains the active user list from the server
                user_list = json.loads(msg['body'])
                menu = om['menu']
                menu.delete(0, "end")
                for user in user_list :
                    if str(user) == str(UID):
                        continue
                    menu.add_command(label=user_list[user], command = lambda v = user_list[user] : om_variable.set(v))
                input_field.focus()
            elif msg['status'] == 202:
                #this message contains user information from the server
                
                #adjust logical clock counter
                while not counter_free: pass
                adjustment_needed = (recv_event_adjustment(counter, msg['event_counter']) > counter + 1)
                counter_free = False
                counter = recv_event_adjustment(counter, msg['event_counter'])
                counter_free = True
                clock_label.configure(text = str(counter))
                
                USERNAME = username_field.get()
                UID = int(msg['body'].split('UID: ')[1])
                #print the message in GUI
                sender = msg['from'].split(' - ')[0]
                mode = msg['from'].split(' - ')[1]
                messages.insert("end", '{}({}): {}\n'.format(sender, mode, msg['body']), "left")
                #send username to the server
                u_body = get_http_req_post(-1, counter + 1, "uname- " + USERNAME)
                send_wait(server, u_body)
            elif msg['status'] == 405:
                #server maxed
                end_chat()
                break
            elif msg['status'] == 406:
                #server closed
                end_chat()
                break
        except BlockingIOError as e:
            continue
        except Exception as e:
            end_chat()
            raise(e)
            
def get_user_list(event, simulated = False):
    global user_list
    global counter
    try:
        user_list = {}
        msg = get_http_req_post(-1, counter + 1, "SEND USER LIST")
        send_wait(server, msg)
        now = time.time()
    except Exception as e:
        print(str(e))

def internal_event_every_second():
    global counter
    global counter_free
    
    while online:
        time.sleep(1)
        if not counter_free: continue
        counter_free = False
        counter  = internal_event_adjustment(counter)
        counter_free = True
        clock_label.configure(text = str(counter))
        
def sending_randomly():
    while online:
        now = time.time()
        time.sleep(random.randint(2, 10))
        print("Slept for: ", int(time.time() - now), " seconds")
        get_user_list(event = None, simulated = True)
        time.sleep(1)
        potential_receivers = [user for user in user_list if user != str(UID)]
        if potential_receivers:
            user = random.choice(potential_receivers)
            print("Sending to: ", user_list[user])
            send_msg(None, '121', user, 'Clock Sync Message')
        else:
            print("No one to send.")
        
#Widgets to show host IP address and port
Label(window, text="Server IP/PORT:").grid(row=0, column=0)
host_label = Label(window, text=str('localhost:8081'))
host_label.grid(row=0, column=1)

#Widget to show logical clock
Label(window, text="Clock:").grid(row=0, column=2)
clock_label = Label(window, text=str('-'))
clock_label.grid(row=0, column=3)

#Widget to get the username
Label(window, text="Username:").grid(row=0, column= 4)
username = StringVar()
username_field = Entry(window, text = username)
username_field.grid(row=0, column = 5)

#Widget for login button
login_button = Button(window, text = 'start', command = start_chat)
login_button.grid(row = 1, column = 1, columnspan = 2)

#Widget for logout button
logout_button = Button(window, text = 'end', state = DISABLED, command = lambda: end_chat(self_end = True))
logout_button.grid(row = 1, column = 3, columnspan = 2)

#Widget for the message box
messages = Text(window)
messages.tag_configure("right", justify="right")
messages.tag_configure("left", justify="left")
messages.grid(row=2, column=0, columnspan=6)

#Widget for the the input from user
text_msg = StringVar()
input_field = Entry(window, text=text_msg, state = DISABLED)
input_field.bind("<Return>", lambda event: send_msg(event, 'BROADCAST'))
input_field.grid(row=3, columnspan = 4, sticky='we')

#Widget for broadcast
broadcast_button = Button(window, text = 'broadcast', state = DISABLED, command = lambda : send_msg(None, 'BROADCAST'))
broadcast_button.grid(row = 3, column = 4)

#Widget for 1 to 1
om_variable = StringVar()
om = OptionMenu(window, om_variable, ())
om_variable.set("select user")
om.configure(width=10)
om.grid(row = 3, column = 5)
om.bind('<1>', get_user_list)
om_variable.trace('w', lambda a,b,c,x="test": send_msg(None, "121", None))

window.protocol('WM_DELETE_WINDOW', lambda: end_chat(self_end = True))
window.mainloop()
