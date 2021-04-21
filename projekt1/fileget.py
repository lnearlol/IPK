#!/usr/bin/env python3
from __future__ import print_function
import argparse
import re
import sys
import os

import socket

def createMessage(serverName):
    return 'WHEREIS '+ serverName +'\r\n'


def createFTP(fileName, serverName):
    return ('GET '+ fileName + ' FSP/1.0\r\n'
    + 'Agent: xstepa64\r\n' 
    + 'Hostname: '+ serverName + '\r\n\r\n')


def fileCopyFTP(TCP_file_name, serverName, fileNameForCreate, TCP_server_adress, TCP_server_port, path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_server_adress, TCP_server_port))
    messageFTP = createFTP(TCP_file_name, serverName)
    sock.sendall(messageFTP.encode())

    filePath = path + '/' + re.sub(fileNameForCreate, '', TCP_file_name)

    try:
        os.makedirs(filePath)
    except OSError:
        try:
            os.chdir(filePath)
        except OSError:
            os.chdir(path)
    else:
        os.chdir(filePath)

    counter = 0
    try:
        with open(fileNameForCreate, 'wb') as f:
            while True:
                try: 
                    sock.settimeout(30)
                    data = sock.recv(1024)
                except socket.timeout:
                    sys.exit('time is over') 
                
                if not data:
                    break
                if(not re.search('FSP/1.0 Success', data.decode('latin-1')) and counter == 0):
                    sys.exit('this file does not exist')
                elif(counter == 0):
                    data = re.sub(b".+?\r\n.+?\r\n\r\n", b'', data)
                f.write(data)
               
                    
                counter+=1

        f.close()
    except PermissionError:
        sys.exit('Permission Error') 
    sock.close()


parser = argparse.ArgumentParser(description='Program needs two arguments')
parser.add_argument('-n', help='IP and port number', required=True)
parser.add_argument('-f', help='Local adress of file', required=True)
args = vars(parser.parse_args())

try:
    # 127.0.0.1
    serverAdress = re.search('^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(?=:)', args['n']).group(0)
    # 3333
    serverPort = int(re.search('(?<=:)[0-9]+$', args['n']).group(0))
    # server.one
    serverName = re.search('(?<=^fsp:\/\/).+?(?=\/)', args['f']).group(0)
    TCP_file_name = re.sub('^fsp://.+?/', '', args['f'])
    fileNameForCreate = re.sub('^fsp://.+/', '', args['f'])
    
    
except AttributeError:
    sys.exit('wrong arguments')



try: 
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = createMessage(serverName)

    clientSocket.sendto(message.encode(), (serverAdress, serverPort))
except socket.gaierror:
    sys.exit('wrong server adress or server port')

try: 
    clientSocket.settimeout(30)
    receivedMessage, serverAddr = clientSocket.recvfrom(4096)
except socket.timeout:
    sys.exit('time is over') 

clientSocket.close()


TCP_server_adress = re.search('(?<=OK ).+(?=:)', receivedMessage.decode('utf-8')).group(0)
TCP_server_port = int(re.search('(?<=:)[0-9]+$', receivedMessage.decode('utf-8')).group(0))


path = os.getcwd()

if(fileNameForCreate == '*'):
    TCP_file_name = 'index'
    fileCopyFTP(TCP_file_name, serverName, 'index', TCP_server_adress, TCP_server_port, path)
    with open('index', 'r') as data:
        for line in data:
            line = re.sub("\n", '', line)
            try:
                fileCopyFTP(line, serverName, re.sub(".*/", '', line), TCP_server_adress, TCP_server_port, path)
            except FileNotFoundError:
                    sys.exit('file not found')
        
else:
    fileCopyFTP(TCP_file_name, serverName, fileNameForCreate, TCP_server_adress, TCP_server_port, path)




