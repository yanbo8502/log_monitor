#!/usr/bin/env python
#  -*- coding:utf-8 -*-
# File send_message.py
import sys
import random
import time,datetime
import urllib2
import pycurl
import StringIO
import urllib
import socket

class sendMessage():
	_phone_numbers = '' #number1,number2,number3....
	_http_api = 'http://xxx.xxxx.xxxx/index.php'
	def __init__(self, phone_numbers):
		print phone_numbers
		self._phone_numbers = phone_numbers


	def set_server(self, server_api):
		self._http_api = server_api

	def send_curl_command(self,url):
		print url
		c = pycurl.Curl()
		c.setopt(c.URL, url)
		b = StringIO.StringIO()
		c.setopt(pycurl.WRITEFUNCTION,b.write)
		c.perform()
		c.close

	def alert_phone_message(self, content):
		#记录报警时间
		check_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time())) + '---'
		ip = self.get_host()
		content =ip + "-" + check_time + content
		
		request_uri = 'phone='+ self._phone_numbers +'&msg='+content
		request_uri_encode = 'phone='+ urllib.quote(self._phone_numbers.encode('utf-8'))+'&msg='+ urllib.quote(content.encode('utf-8'))
		cmd_email = self._http_api + '?' + request_uri
		cmd_email_encode = self._http_api + '?' + request_uri_encode
		print cmd_email
		self.send_curl_command(cmd_email_encode)

	def get_host(self):
		skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#连接8.8.8.8，8.8.8.8是google提供的公共dns服务器
		skt.connect(('8.8.8.8',80))
		#获得连接信息，是一个tuple （ip，port）
		socketIpPort = skt.getsockname()
		ip = socketIpPort[0]
		skt.close()
		return ip

