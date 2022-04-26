#!/usr/bin/env python3

from mailbox import NotEmptyError
import socket
import os
import sys
import signal
import hashlib

def header_split(header):

    header = header.strip()
    header = header.split(':')

    id = ''
    value = ''
    char = ''
    
    if (len(header)!=2):
        return id, value

    if not header[0].isascii():
        return id, value
    
    if (header[0].find(':')!=-1):
        return id, value
    
    if char in header[0]:
        if (char.isspace()):
            return id, value
    
    if (header[1].find('/')!=-1):
        return id, value
    
    id = header[0]
    value = header[1]

    return id, value

def method_read(headers):

    status_code=100
    status_message='OK'

    reply_header=''
    reply_content=[]

    try:
        with open(f'data/{headers["File"]}','r') as file:
            lines=file.readlines()
            if int(headers["From"]) > int(headers["To"]):
                status_code,status_message=(200,'Bad request')
            else:
                for i in range (int(headers["From"]),int(headers["To"])):
                    reply_content.append(lines[i].strip())
                reply_header=f'Lines:{len(reply_content)}\n'    
            
    except ValueError:
        status_code,status_message=(200,'Bad request')
    except KeyError:
        status_code,status_message=(200,'Bad request')
    except IndexError:
        status_code,status_message=(201,'Bad line number')
    except FileNotFoundError:
        status_code,status_message=(202,'No such file')
    except OSError:
        status_code,status_message=(203,'Read error')

    return status_code,status_message,reply_header,reply_content

def method_ls():

    status_code=100
    status_message='OK'

    reply_header=''
    reply_content=[]

    dir = os.listdir(f'data')
    dir = sorted(dir,reverse=True)
    reply_header = f'Lines:{len(dir)}\n'

    for i in range (len(dir)):
        reply_content.append(dir[i].strip())

    return status_code,status_message,reply_header,reply_content

def method_length(headers):

    status_code=100
    status_message='OK'

    reply_header=''
    reply_content=[]

    try:
        with open(f'data/{headers["File"]}','r') as file:
            lines=file.readlines()
            if len(lines) >= 0:
                reply_header=f'Lines: 1\n' 
            reply_content.append(len(lines))  
            
    except ValueError:
        status_code,status_message=(200,'Bad request')
    except KeyError:
        status_code,status_message=(200,'Bad request')
    except FileNotFoundError:
        status_code,status_message=(202,'No such file')
    except OSError:
        status_code,status_message=(203,'Read error')

    return status_code,status_message,reply_header,reply_content

s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('',9999))
signal.signal(signal.SIGCHLD,signal.SIG_IGN)
s.listen(5)

status_code=100
status_message='OK'

method=''

headers={}
header=''
header_id=''
header_value=''

reply_header=''
reply_content=[]

while True:

    client_socket,client_adress=s.accept()
    print(f'Connection with {client_adress}')
    pid_child=os.fork()

    if pid_child == 0:
        s.close()
        f=client_socket.makefile('rwb')

        while True:

            method = f.readline().decode('utf-8')
            method = method.strip()

            if not method:
                break

            header = f.readline().decode('utf-8')

            while header != '\n':
                header_id,header_value=header_split(header)
                headers[header_id]=header_value

                header=f.readline().decode('utf-8')

            print(f'method:{method}')

            if method=='READ':
                status_code,status_message,reply_header,reply_content=method_read(headers)
            elif method=='LS':
                status_code,status_message,reply_header,reply_content=method_ls()
            elif method=='LENGTH':
                status_code,status_message,reply_header,reply_content=method_length(headers)
            else:
                status_code,status_message=(204,'Unknown method')

                f.write(f'{status_code} {status_message}\n'.encode('utf-8'))
                f.flush()
                sys.exit(0)
            
            f.write(f'{status_code} {status_message}\n'.encode('utf-8'))
            f.write(f'{reply_header}\n'.encode('utf-8'))
            f.flush()

            for i in range (len(reply_content)):
                    f.write(f'{reply_content[i]}\n'.encode('utf-8'))
                    f.flush()

        print(f'{client_adress} connection ended')
        sys.exit(0)
    
    else:
        client_socket.close()
