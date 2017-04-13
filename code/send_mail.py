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

	def alert_emails(self,email_subject,email_content):
		#记录报警时间
		check_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time())) + '---'
		ip = self.get_host()
		email_subject =  email_subject  + "-" + ip 
		email_content = check_time + email_content
		request_uri_data = {}
 		request_uri_data["to"] = self._mail_adresses 
		request_uri_data["title"] = email_subject
		request_uri_data["html"] = email_content

		self.send_curl_post_command(self._http_api, request_uri_data)

	def get_host(self):
		skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#连接8.8.8.8，8.8.8.8是google提供的公共dns服务器
		skt.connect(('8.8.8.8',80))
		#获得连接信息，是一个tuple （ip，port）
		socketIpPort = skt.getsockname()
		ip = socketIpPort[0]
		skt.close()
		return ip


	def send_email_bin(self, email_subject, email_content):
		try:
			check_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time())) + '---'
			email_content = urllib.quote(check_time + email_content)
			email_subject = urllib.quote(email_subject + ' ' + self.get_host())
			send_mail_cmd='/bin/bd.talk %s %s %s' % (self._mail_adresses, email_subject, email_content)
			send_mail_args = shlex.split(send_mail_cmd)
			subprocess.Popen(send_mail_args)
		except Exception as e:
			print e

if __name__ == '__main__':

	if len(sys.argv)<4:
		print "cmd <mail_list> <mail_title> <mail_body>"
		exit(1)

	a = sendMail(sys.argv[1])

	a.set_server('http://10.180.92.210:9110/bigdata/common_service/v0/send_mail')
	a.alert_emails(sys.argv[2],sys.argv[3])

