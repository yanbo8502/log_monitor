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

	def send_curl_get_command(self,base_url,request_uri_data):
		request_uri_encode = urllib.urlencode(request_uri_data)
		url =  base_url + '?' + request_uri_encode
		print url
		c = pycurl.Curl()
		c.setopt(c.URL, url)
		b = StringIO.StringIO()
		c.setopt(pycurl.WRITEFUNCTION,b.write)
		c.perform()
		c.close

	def send_curl_post_command(self,base_url,request_uri_data):

		c = pycurl.Curl()
		c.setopt(pycurl.VERBOSE,1)
		c.setopt(pycurl.FOLLOWLOCATION, 1)
		c.setopt(pycurl.MAXREDIRS, 5)
		#crl.setopt(pycurl.AUTOREFERER,1)
		c.setopt(pycurl.CONNECTTIMEOUT, 60)
		c.setopt(pycurl.TIMEOUT, 300)
		#crl.setopt(pycurl.PROXY,proxy)
		c.setopt(pycurl.HTTPPROXYTUNNEL,1)
		#crl.setopt(pycurl.NOSIGNAL, 1)
		c.setopt(pycurl.USERAGENT, "sendmail.py")
		# Option -d/--data <data>  HTTP POST data
		c.setopt(c.POSTFIELDS, urllib.urlencode(request_uri_data))
		#c.setopt(c.POSTFIELDS, "to=yanbo@le.com&title=123&html=456")
		c.setopt(c.URL, base_url)
		b = StringIO.StringIO()
		c.setopt(pycurl.WRITEFUNCTION,b.write)
		c.perform()
		c.close

	def alert_phone_message(self, content):
		#记录报警时间

		check_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))
		ip = self.get_host()
		content =ip + '-' + content + '-' + check_time

		request_uri_data = {}
 		request_uri_data["phone"] = self._phone_numbers 
		request_uri_data["msg"] = content		

		self.send_curl_get_command(self._http_api, request_uri_data)

	def get_host(self):
		skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#连接8.8.8.8，8.8.8.8是google提供的公共dns服务器
		skt.connect(('8.8.8.8',80))
		#获得连接信息，是一个tuple （ip，port）
		socketIpPort = skt.getsockname()
		ip = socketIpPort[0]
		skt.close()
		return ip

if __name__ == '__main__':
	
	if len(sys.argv)<3:
		print "cmd <phone_list>  <message_body>"
		exit(1)

	a = sendMessage(sys.argv[1])

	a.set_server('http://sms.bops.live/index.php')
	a.alert_phone_message(sys.argv[2])

