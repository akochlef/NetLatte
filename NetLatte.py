#! /usr/bin/python

# NetLatte
# Created by: Anis Kochlef
# Measures network delays and packet loss


import random
import string
import json
import time
import datetime
import sys
import _thread
import socket

__VERSION__ = '1.0'
__ID__ = 'NetLatte'
__MESSAGE_SIZE__ = 1216
__BUFFER_SIZE__ = 1600
__SLEEP_TIME__ = 0.1
__MAX_BLOCK_SIZE_IN_DAYS__ = 14
__MAX_BLOCK_SIZE__ = round(__MAX_BLOCK_SIZE_IN_DAYS__*24*60*60/__SLEEP_TIME__)
__SERVER_LISTEN_IP__ = '0.0.0.0'
__LOG_FILE__ = 'netlatte.log'

def save_log(filename,line):
	file_object = open(filename, 'a')
	file_object.write(line)
	file_object.write('\n')
	file_object.close()

def rand_message(size):
	msg = ''
	for i in range(size):
		msg += random.choice(string.ascii_letters)
	return msg

def number_of_lost_packets(previous_block,previous_index,block,index):
	loss = -999
	if((previous_block==block)and(index>previous_index)):
		loss = index-previous_index-1
	else:
		if(previous_block<block):
			loss = __MAX_BLOCK_SIZE__*(block-previous_block) + index - previous_index - 1
		else:
			if((previous_block==__MAX_BLOCK_SIZE__-1) and (previous_index==__MAX_BLOCK_SIZE__-1)):
				loss = __MAX_BLOCK_SIZE__*block+index
	return loss
		

def server(listen_ip,listen_port):
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.bind((listen_ip,listen_port))
	while True:
		data, addr = sock.recvfrom(1600)
		sock.sendto(data,addr)


def sender(sock,server_ip,server_port,message,sleep_time,max_block_size):
	b = 0
	i = 0
	while True:
		ts = time.time()
		dm = {'block': b,'index': i,'timestamp': ts,'payload': message}
		jm = json.dumps(dm)
		bm = bytes(jm,'utf-8')
		sock.sendto(bm,(server_ip, server_port))
		time.sleep(sleep_time)
		i += 1
		if(i == max_block_size):
			i = 0
			b += 1
			if(b == max_block_size):
				b = 0
		
		
def reciever(sock,log_file):
	previous_ts = time.time()
	previous_block = 0
	previous_index = -1
	
	while True:
		bm, addr = sock.recvfrom(__BUFFER_SIZE__)
		msg = bm.decode('utf-8')
		jm = json.loads(msg)
		msg_ts = jm.get('timestamp')
		msg_block = jm.get('block')
		msg_index = jm.get('index')
		ts = time.time()
		loss = number_of_lost_packets(previous_block,previous_index,msg_block,msg_index)
		if(loss != 0):
			td = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
			duration = round((ts-previous_ts)*1000)/1000
			log = f'[{__ID__}] {td} Network interruption detected (duration= {duration} s, loss={loss} packets)'
			print(log)
			save_log(log_file,log)
		previous_ts = msg_ts
		previous_block = msg_block
		previous_index = msg_index
	
def client(server_ip,server_port,message_size,sleep_time,max_block_size,log_file):
	rm = rand_message(message_size)
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	_thread.start_new_thread(sender,(sock,server_ip,server_port,rm,sleep_time,max_block_size))
	_thread.start_new_thread(reciever(sock,log_file))
	
if __name__ == "__main__":
	if (len(sys.argv)==3 and sys.argv[1]=='-s'):
		port = int(sys.argv[2])
		server(__SERVER_LISTEN_IP__,port)
		
	if (len(sys.argv)==4 and sys.argv[1]=='-c'):
		ip = sys.argv[2]
		port = int(sys.argv[3])
		client(ip,port,__MESSAGE_SIZE__,__SLEEP_TIME__,__MAX_BLOCK_SIZE__,__LOG_FILE__)
	
		









