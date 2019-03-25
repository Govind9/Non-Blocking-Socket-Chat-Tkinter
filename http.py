#Name: Karanjeet Singh
#UID: 1001703147
#LoginId:Kxs3147


import time

version = '1.0'
user_agent = 'Mozilla/4.0 (compatible; MSIE5.01; Windows NT)'
host = 'localhost'
dt_format = '%a, %d %b %Y %H:%M:%S GMT'
status_codes = {
    200: 'OK',
    201: 'Active User List',
    202: 'User Information',
    500: 'Internal Server Error', 
    404: 'Client Offline', 
    405: 'Server Maxed', 
    406: 'Server Closed'
}


def get_http_req_post(recv, counter = -1, msg_body = ''):
    http_string =  'POST {} HTTP/{}\n'.format(recv, version)
    http_string += 'User-Agent: {}\n'.format(user_agent)
    http_string += 'Host: {}\n'.format(host)
    http_string += 'From: {}\n'.format('NA')
    http_string += 'Date: {}\n'.format(time.strftime(dt_format, time.gmtime(time.time())))
    http_string += 'Event-Counter: {}\n'.format(counter)
    http_string += 'Content-Length: {}\n'.format(len(msg_body))
    http_string += '\n'
    http_string += msg_body
    
    return http_string
    
def get_http_req_get(counter = -1):
    http_string =  'GET server HTTP/{}\n'.format(version)
    http_string += 'User-Agent: {}\n'.format(user_agent)
    http_string += 'Host: {}\n'.format(host)
    http_string += 'From: {}\n'.format('NA')
    http_string += 'Date: {}\n'.format(time.strftime(dt_format, time.gmtime(time.time())))
    http_string += 'Event-Counter: {}\n'.format(counter)
    http_string += 'Content-Length: 0\n'
    
    return http_string
    
def get_http_res(source, status = 200, msg_body = '', mode = '1', counter = -1):
    http_string =  'HTTP/{} {} {}\n'.format(version, status, status_codes[status])
    http_string += 'User-Agent: {}\n'.format(user_agent)
    http_string += 'Host: {}\n'.format(host)
    http_string += 'From: {} - {}\n'.format(source, mode)
    http_string += 'Date: {}\n'.format(time.strftime(dt_format, time.gmtime(time.time())))
    http_string += 'Event-Counter: {}\n'.format(counter)
    http_string += 'Content-Length: {}\n'.format(len(msg_body))
    http_string += '\n'
    http_string += msg_body
    
    return http_string
    
def parse_http_string(http_string):
    ret = {
        'type': None,
        'user_agent': None,
        'host': None,
        'from': None,
        'date': None,
        'content_length': None,
        'event_counter': -1,
        'recv': None,
        'body': None,
        'status': None
    }
    http = http_string.splitlines()
    try:
        if 'GET' in http[0]: 
            ret['type'] = 'GET'
            ret['recv'] = 'server'
        elif 'POST' in http[0]: 
            ret['type'] = 'POST'
            ret['recv'] = int(http[0].split('POST ')[1].split(' HTTP')[0])
            ret['body'] = '\n'.join(http[8:])
        else: 
            ret['type'] = 'RES'
            ret['status'] = int(http[0].split(' ')[1])
            ret['body'] = '\n'.join(http[8:])
        
        ret['user_agent'] = http[1].split('User-Agent: ')[1]
        ret['host'] = http[2].split('Host: ')[1]
        ret['from'] = http[3].split('From: ')[1]
        ret['date'] = http[4].split('Date: ')[1]
        ret['event_counter'] = int(http[5].split('Event-Counter: ')[1])
        ret['content_length'] = int(http[6].split('Content-Length: ')[1])
        
        return ret
    except Exception as e:
        ret['body'] = str(e)
        return ret
    
    
    
    
