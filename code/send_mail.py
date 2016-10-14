#!/usr/bin/env python
#  -*- coding:utf-8 -*-
# File send_mail.py
import sys
import random
import time,datetime
import urllib2
import pycurl
import StringIO
import urllib
import socket

class sendMail():
	_mail_adresses = ''
	_http_api = 'http://xxxx.xxxxx.xxxx/mail.php'

	def __init__(self, mail_adresses):
		self._mail_adresses = mail_adresses

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

	def alert_emails(self,email_subject,email_content):
		#记录报警时间
		check_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time())) + '---'
		ip = self.get_host()
		email_subject = ip + "-" + email_subject
		email_content =check_time + email_content
 
		request_uri = 'sendto='+ self._mail_adresses +'&subject='+email_subject+'&body=' + email_content
		request_uri_encode = 'sendto='+ urllib.quote(self._mail_adresses.encode('utf-8'))+'&subject='+ urllib.quote(email_subject.encode('utf-8'))+'&body=' + urllib.quote(email_content.encode('utf-8')) 
		cmd_email = self._http_api + '?' + request_uri
		cmd_email_encode = self._http_api + '?' + request_uri_encode
		
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

