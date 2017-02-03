#!/usr/bin/env python
# -*- coding:utf-8 -*-
#./log_monitor.py ~/Codes/datamining_server_scripts/code/system_monitor/log_monitor.ini ~/Codes/dmp_letv_matrix_web/spring-boot-samples/catalina.base_IS_UNDEFINED/logs/dmp

'''
    @author:   yanbo
    @desc:     control frequency of continuous repeated actions such as alert. 
    @date:     2017-01-12
    @lastUpdate yanbo 2017-01-12
'''
import sys
import re
import random
import StringIO
import ConfigParser
import os
import time,datetime
import json
import send_mail
import send_message
import math

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

class FrequencyControl():
	_config_path = ""
	_phone_list = []
	_email_list = []
	_mail_handler = send_mail.sendMail("")
	_message_handler = send_message.sendMessage("")
	_cache_path = ""


	def __init__(self, config_path, cache_path, source_key):
		self._group_size = 5
		self._config_path = config_path		
		self.conf = ConfigParser.ConfigParser()
		self.conf.read(self._config_path)
		self.email_list = []

		if  '' == cache_path:
			filebasename = os.path.basename(config_path)
			self._cache_path =  filebasename + '.' + source_key + ".alert.cache"
		else:
			self._cache_path = cache_path

		f = open(self._cache_path, 'a+')
		f.close()

		self.cache_conf =  ConfigParser.ConfigParser()
		self.cache_conf.read(self._cache_path)

		_email_list_str = self.conf.get("basic",'emails')
		_phone_list_str = self.conf.get("basic",'phones')
		mail_server = self.conf.get("basic",'mail_server')
		message_server = self.conf.get("basic",'message_server')
					
		self._mail_handler = send_mail.sendMail(_email_list_str)
		self._message_handler = send_message.sendMessage(_phone_list_str)
		self._mail_handler.set_server(mail_server)
		self._message_handler.set_server(message_server)
	
	'''
	@monitor_item 	string
	@status 		bool
	@min_interval   int
	@title 			string
	@body  			string
	@need_message	bool
	@need_mail		bool
	'''
 
	def alert_control(self, monitor_item, is_error, stat_interval, title, body, need_message, need_mail):		
		continuous_error_stat_count = 0
		alert_count = 0
		last_alert_time = 0l
		print monitor_item
		#load cache
		try:
			continuous_error_stat_count = int(self.cache_conf.get(monitor_item,'continuous_error_stat_count'))			
		except Exception,e:
			print e

		try:
			alert_count = int(self.cache_conf.get(monitor_item,'alert_count'))			
		except Exception,e:
			print e

		try:
			last_alert_time = long(self.cache_conf.get(monitor_item,'last_alert_time'))			
		except Exception,e:
			print e

		if is_error:
			continuous_error_stat_count = continuous_error_stat_count + 1
		else:
			continuous_error_stat_count = 0
			alert_count = 0
		
		#(is_send, alert_min_duration) = self.alert_judge_v1(continuous_error_stat_count, stat_interval)
		#(is_send, alert_min_duration) = self.alert_judge_v2(continuous_error_stat_count, stat_interval)
		(is_send, alert_min_duration) = self.alert_judge_v3(is_error, alert_count, last_alert_time, stat_interval)
		if is_send:
			if need_message:
				self._message_handler.alert_phone_message(title + " " + body)
			if need_mail:
				self._mail_handler.alert_emails(title, body)
			alert_count = alert_count + 1
			last_alert_time = long(time.time())

		self.set_cache_value_dynamic(monitor_item,'continuous_error_stat_count',continuous_error_stat_count)
		self.set_cache_value_dynamic(monitor_item,'alert_count',alert_count)
		self.set_cache_value_dynamic(monitor_item,'last_alert_time',last_alert_time)
		self.set_cache_value_dynamic(monitor_item,'alert_min_duration',alert_min_duration)

		return continuous_error_stat_count


	def alert_judge_v1(self, continuous_error_stat_count, stat_interval):

		is_send = False
		frequency_factor = 1

		if continuous_error_stat_count!=0:
			count_groups = 1.0*continuous_error_stat_count/self._group_size + 1
			exp = int((math.log(count_groups)/math.log(2)))
			frequency_factor = 2**exp
		
		max_factor = int(3600/stat_interval)

		if frequency_factor>max_factor:
			frequency_factor = max_factor

		if continuous_error_stat_count!=0 and continuous_error_stat_count%frequency_factor == 0:
			is_send = True

		alert_min_duration = stat_interval * frequency_factor
		print "frequency_factor:"  + str(frequency_factor)
		print "continuous_error_stat_count:"  + str(continuous_error_stat_count)

		return is_send, alert_min_duration

	def alert_judge_v2(self, continuous_error_stat_count, stat_interval):

		is_send = False
		frequency_factor = 1
		total_count = 0
		total_count = total_count + self._group_size * frequency_factor
		alert_min_duration = 0
		while total_count<continuous_error_stat_count:
			total_count = total_count + self._group_size * frequency_factor
			frequency_factor = frequency_factor * 2
			alert_min_duration = stat_interval * frequency_factor
			if frequency_factor*stat_interval > 3600:
				alert_min_duration = 3600
				break

		if continuous_error_stat_count!=0 and continuous_error_stat_count%frequency_factor == 0:
			is_send = True

		print "frequency_factor:"  + str(frequency_factor)
		print "continuous_error_stat_count:"  + str(continuous_error_stat_count)

		return is_send, alert_min_duration

	def alert_judge_v3(self, is_error, alert_count, last_alert_time, min_alert_interval):
		is_send = False
		alert_duration_factor = alert_count/self._group_size + 1
		alert_min_duration = min_alert_interval * alert_duration_factor
		current_time = time.time()
		if is_error and (current_time - last_alert_time) > alert_min_duration:
			is_send = True

		return is_send,alert_min_duration



	def set_cache_value_dynamic(self,section,section_para_name, section_para_value):
		cfd = open(self._cache_path, 'w')
		if section not in self.cache_conf.sections():
			self.cache_conf.add_section(section)
		self.cache_conf.set(section, section_para_name, section_para_value)
		self.cache_conf.write(cfd)
		cfd.close()

import getopt

def PrintHelp():
	print "-c/--config= <config path>"
	print "-b/--body= <message body, optional,default is empty>"
	print "-t/--title= <message title>"
	print "-k/--key= <alert source key> to indentify the different alert source to apply different rules and caches"
	print '--target= <alert target>'
	print "--error= <is error need alert>"
	print "--interval= <min alert inerval, optional>,unit is second, default is 300"


if __name__ == '__main__':

	shortargs = 'c:b:t:k:h'
	longargs = ['body=', 'config=', 'title=','alert_target=', 'key=', 'error=','interval=']
	opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs)   

	config_path =''
	body = ''
	title = ''
	key = ""
	error = False
	interval = 300
	arg_count = 0
	error_str = ''
	print_help = False
	alert_target = ''

	for opt, value in opts:
		if '-h' == opt:
			print_help = True
		if '-c' == opt:
			config_path = value
		if '--config' == opt:
			config_path = value
		if '-t' == opt:
			title = value
		if '--title' == opt:
			title = value	
		if '-b' == opt:
			body = value
		if '--body' == opt:
			body = value			
		if '-k' == opt:
			key = value
		if '--key' == opt:
			key = value
		if '--alert_target' == opt:
			alert_target = value
		if '--error' == opt:
			error = bool(value)
			error_str = value
		if '--interval' == opt:
			interval = int(value)

	if print_help or '' == config_path   or ''== key  or '' == alert_target or '' == error_str   or '' == title:
		PrintHelp()
		exit(0)

	print "config_path: " + config_path

	control = FrequencyControl(config_path, "", key)	
	control.alert_control(alert_target, error, interval, title, body, True, True)
