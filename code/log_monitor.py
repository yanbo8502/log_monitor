#!/usr/bin/env python
# -*- coding:utf-8 -*-
#./log_monitor.py ~/Codes/datamining_server_scripts/code/system_monitor/log_monitor.ini ~/Codes/dmp_letv_matrix_web/spring-boot-samples/catalina.base_IS_UNDEFINED/logs/dmp

'''
    @author:   yanbo
    @desc:     log monitor 
    @date:     2015-6-16
    @lastUpdate yanbo 2017-01-12
'''
import sys
import re
import time
import os
import random
import datetime
import pycurl
import StringIO
import urllib
import ConfigParser
import json
import urllib2 
import log_stats_for_time_module
import send_mail
import send_message
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import frequency_control

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

class logMonitor():
	_config_path = ""
	_target_log_path = ""
	_log_type = ""
	_phone_list = []
	_email_list = []
	_mail_handler = send_mail.sendMail("")
	_message_handler = send_message.sendMessage("")
	_cache_path = ""
	_start_line_number = 0
	_end_line_number = 0
	_target_file_list = []
	_target_log_db_uri = ""
	_target_log_db_dbname = ""
	_target_log_db_tablename = ""
	_instance_key = "default"
	_log_rotate = True

	def __init__(self, config_path, cache_path, target_log_path, instance_key):
		self._config_path = config_path
		self._target_log_path = target_log_path
		if '' != instance_key:
			self._instance_key = instance_key

		self.conf = ConfigParser.ConfigParser()
		self.conf.read(self._config_path)
		self.email_list = []
		self.log_name_prefix = ''
		self._log_type = self.conf.get('basic','log_type')

		if  '' == cache_path:
			filebasename = os.path.basename(config_path)
			self._cache_path =  filebasename + '.' + self._instance_key + ".cache"
		else:
			self._cache_path = cache_path

		f = open(self._cache_path, 'a+')
		f.close()

		self.cache_conf =  ConfigParser.ConfigParser()
		self.cache_conf.read(self._cache_path)

		self._freq_control = frequency_control.FrequencyControl(self._config_path, "", self._instance_key)


	def task_portal(self):

		section_list = self.conf.sections()
		monitor_list = []

		for item in section_list:
			if item == 'basic':
				if self.conf.get(item,'enable') == 'false':
					return
				else:
					try: 
						log_dir = self.conf.get(item,'log_dir')
						if '' == self._target_log_path:
							self._target_log_path = log_dir
					
					except Exception,e:
						print str(e)
					if '/' == self._target_log_path[len(self._target_log_path) -1]:
						self._target_log_path = self._target_log_path[0:len(self._target_log_path) -1]
					
					print "_target_log_path: " + self._target_log_path

					self.log_name_prefix = self.conf.get(item,'log_name_prefix')
					self.log_name_everyday()
					self._email_list = self.conf.get(item,'emails').split(',')
					self._phone_list = self.conf.get(item,'phones').split(',')
					_email_list_str = self.conf.get(item,'emails')
					_phone_list_str = self.conf.get(item,'phones')
					mail_server = self.conf.get(item,'mail_server')
					message_server = self.conf.get(item,'message_server')
					
					self._mail_handler = send_mail.sendMail(_email_list_str)
					self._message_handler = send_message.sendMessage(_phone_list_str)
					self._mail_handler.set_server(mail_server)
					self._message_handler.set_server(message_server)
			else:
				if self.conf.get(item,'enable') != 'false':
					monitor_list.append(item)


		#get scanning and processing settings and cached data of last scanning
		self._target_file_list, self._start_line_number = self.get_increased_file_path_list('basic')

		print self._target_file_list
		print self._start_line_number

		self._end_line_number = 0
		last_file_path = ""
		file_count = len(self._target_file_list)

		if file_count >= 1:
			last_file_path = self._target_file_list[file_count -1]
			self._end_line_number = self.get_file_length(last_file_path)

		for monitor_item in monitor_list:
			try:
				self.worker(monitor_item)
				#raise Exception('test')
			except Exception,e:
				print str(e)
				error_message = monitor_item + 'catch exception: ' + str(e)
				print error_message
				self.record_error_message(error_message)

		if file_count < 1:
			return
		self.set_cache_value_dynamic("basic",'lines', self._end_line_number)
		self.set_cache_value_dynamic("basic",'last_file',last_file_path) 

	def worker(self,monitor_item):
			
		if monitor_item == 'error_words_monitor':
			if self.conf.get(monitor_item,'monitor_words') == '':
				return
			print 'error_words_monitor start'
			self.error_words_monitor(self._target_file_list, self._start_line_number, self._end_line_number)
		elif monitor_item == 'target_words_monitor':
			print 'target_words_monitor start'
			self.target_words_monitor(self._target_file_list, self._start_line_number, self._end_line_number)
		elif monitor_item == 'user_request_monitor':
			print 'user_request_monitor start'
			self.log_query_record_monitor(self._target_file_list, self._start_line_number, self._end_line_number)
		elif monitor_item == 'overtime_monitor':
			print 'overtime_monitor start'
			self.overtime_monitor(self._target_file_list, self._start_line_number, self._end_line_number)
		elif monitor_item == 'error_status_monitor':
			print 'error_status_monitor start'
			self.error_status_monitor(self._target_file_list, self._start_line_number, self._end_line_number)
		
		else:
			return

	def log_name_everyday(self):

		today = datetime.datetime.today()
		try:
			date = today.strftime("%Y-%m-%d")
			print self.log_name_prefix
		except Exception,e:
			print str(e)
			return

	def target_words_monitor(self, target_file_list, start_line_number, end_line_number):
	
		end_line_number = 0
		last_file_path = ""
		file_count = len(target_file_list)
		file_index = 0
		for file_path in target_file_list:		
		#beginning scanning file content
			if file_index < file_count-1:
				file_end = self.process_target_words_by_settings('target_words_monitor', file_path, start_line_number, 0)
			else:
				file_end = self.process_target_words_by_settings('target_words_monitor', file_path, start_line_number, end_line_number)

			start_line_number = 0
			file_index = file_index + 1


	def error_words_monitor(self, target_file_list, start_line_number, end_line_number):
		#LOAD CONFIG
		stats_interval_str = self.conf.get('error_words_monitor','stats_interval');
		count_thrshold_str = self.conf.get('error_words_monitor','count_threshold');
		email_subject = self.conf.get('error_words_monitor','email_subject')
		email_content = self.conf.get('error_words_monitor','email_content')
		stats_intervals = json.loads(stats_interval_str)
		count_thresholds = json.loads(count_thrshold_str)
		monitor_words_list = count_thresholds.keys()
		monitor_words_list =  self.conf.get('error_words_monitor','monitor_words').split(',');
	
		#LOAD CACHE
		print 'load cache'
		counts=  {} 
		start_times =  {}
		try:
			count_cache_str = self.cache_conf.get('error_words_monitor','count');
			counts = json.loads(count_cache_str)
		except Exception,e:
			for word in monitor_words_list:
				counts[word] = 0
			print str(e)

		try:
			start_time_cache_str = self.cache_conf.get('error_words_monitor','start_time');
			start_times = json.loads(start_time_cache_str)
		except Exception,e:
			for word in monitor_words_list:
				start_times[word] = long(time.time())
			print str(e)
		
		#load finish
		print 'load finish'
		

		#get scanning and processing settings and cached data of last scanning
		words_count_list = []
		words_count_thresholds = []
		#beginning scanning file content
		increased_words_count_list = self.process_error_words_by_settings(target_file_list, monitor_words_list, start_line_number, end_line_number)
		print increased_words_count_list	
		for index in range(0, len(monitor_words_list)):
			word = monitor_words_list[index]
			#use cache data
			threshold = count_thresholds[word]
			word_count = increased_words_count_list[index] + counts[word]				
			start_time = start_times[word]
			stats_interval =  stats_intervals[word]

			counts[word] = word_count
			current_time = long(time.time())
			total_time = current_time - long(start_time)
			title = ""
			body = ""
			is_error = False
			need_freq_control = False
			#update by count
			print word + "," + str(word_count) + "," + str(threshold)
			if word_count >= int(threshold) and total_time>=stats_interval:
					
				start_time_str = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(start_time))
				 
				body =  email_subject + " " + email_content +  ' [' + word + ']' + ' threshold: ' + str(threshold) +\
				 ' exact count:' + str(word_count) + ' from ' + start_time_str + " within statistic period " + str(total_time) + " s"
				title = email_subject + ' [' + word + ']'
				is_error = True

			if total_time>=stats_interval:
				need_freq_control = True
		
			if need_freq_control:
				self._freq_control.alert_control("error_words_monitor" + word, is_error, stats_interval, title, body, True, True)

			if  total_time >= stats_interval:
				start_times[word] = current_time
				counts[word] = 0
				print word

		#update cache
		print 'update cache'
		count_cache_str = json.dumps(counts)
		start_time_str =  json.dumps(start_times)
		self.set_cache_value_dynamic("error_words_monitor",'count', count_cache_str)
		self.set_cache_value_dynamic("error_words_monitor",'start_time', start_time_str)
		

	def overtime_monitor(self, target_file_list, start_line_number, end_line_number):

		#get scanning and processing settings and cached data of last scanning
	
		overtime_ratio_threshold = float(self.conf.get('overtime_monitor','overtime_ratio_threshold'))
		time_threshold = int(self.conf.get('overtime_monitor','time_threshold'))

		print time_threshold
		print overtime_ratio_threshold		
		
		#beginning scanning file content
		self.process_overtime_by_settings('overtime_monitor', target_file_list, start_line_number, end_line_number, overtime_ratio_threshold, time_threshold)

	def log_query_record_monitor(self, target_file_list, start_line_number, end_line_number):
		
		monitor_words_list = self.conf.get('user_request_monitor','target_words').split(',')		
		keyword = monitor_words_list[0]
		print keyword

		log_paras_indice = {}
		log_paras_type = {}
		timestamp_unit = 's'
		log_regx = ""

		time_format = self.conf.get('user_request_monitor', 'time_format')
		self._target_log_db_uri = self.conf.get('user_request_monitor', 'target_db_uri')
		self._target_log_db_dbname = self.conf.get('user_request_monitor', 'db_name')
		self._target_log_db_tablename = self.conf.get('user_request_monitor', 'table_name')
		try:
			self._log_rotate = self.conf.get('user_request_monitor', 'log_daily_rotate') == 'true'
		except Exception,ex:
			print ex 

		try:
			log_paras_type = eval(self.conf.get('user_request_monitor', 'log_paras_type'))
			timestamp_unit = self.conf.get('user_request_monitor', 'timestamp_unit')
		except Exception,ex:
			print ex

		if "regx" == self._log_type or "csv" == self._log_type:
			log_paras_indice = eval(self.conf.get('user_request_monitor', 'log_paras_indice'))

		if "regx" == self._log_type:
			log_regx = self.conf.get('user_request_monitor', 'log_regx')

		#get scanning and processing settings and cached data of last scanning
		file_index = 0
		file_count = len(target_file_list)
		record_count = 0
		for file_path in target_file_list:
			if file_index == file_count -1: 
				record_count += self.ReadTargetRecordInFile(file_path, keyword, start_line_number, end_line_number, log_regx, log_paras_indice, log_paras_type, time_format, timestamp_unit)
			else:
				record_count += self.ReadTargetRecordInFile(file_path, keyword, start_line_number, 0, log_regx, log_paras_indice, log_paras_type, time_format, timestamp_unit)
			file_index = file_index +1
			start_line_number = 0

		print 'Totally upload ' + str(record_count) + ' to db'

	def error_status_monitor(self, target_file_list, start_line_number, end_line_number):
		monitor_item = 'error_status_monitor'
		#load config
		monitor_words_list_str = self.conf.get(monitor_item,'monitor_words')
		monitor_words_list = monitor_words_list_str.split(',')		
		filter_pattern = self.conf.get(monitor_item,'filter_pattern')
		stats_interval = long(self.conf.get(monitor_item,'stats_interval'))
		error_status_ratio_threshold = float(self.conf.get('error_status_monitor','error_ratio_threshold'))
		email_subject = self.conf.get(monitor_item,'email_subject')
		email_content = self.conf.get(monitor_item,'email_content')
		
		start_time = 0l
		total_error_count = 0l
		total_query_count = 0l

		#load cache
		try:
			start_time = long(self.cache_conf.get(monitor_item,'start_time'))			
			total_error_count = long(self.cache_conf.get(monitor_item,'error_count'))
			total_query_count = long(self.cache_conf.get(monitor_item,'query_count'))
		except Exception,e:
			print e
		#get scanning and processing settings and cached data of last scanning
		file_index = 0
		file_count = len(target_file_list)

		file_total_line_count = 0 
		file_error_line_count = 0
		total_line_count = 0
		error_line_count = 0
		for file_path in target_file_list:
			if file_index == file_count -1: 
				file_total_line_count, file_error_line_count = self.process_single_file_error_status(file_path, filter_pattern, monitor_words_list, start_line_number, end_line_number)
			else:
				file_total_line_count, file_error_line_count = self.process_single_file_error_status(file_path, filter_pattern, monitor_words_list, start_line_number, 0)
			
			total_line_count += file_total_line_count
			error_line_count += file_error_line_count

			file_index = file_index +1
			start_line_number = 0

		
		total_query_count += total_line_count
		total_error_count += error_line_count

		error_status_ratio = 0.0
		if total_query_count > 0:
			error_status_ratio = round(total_error_count*1.0/total_query_count,2)
		

		current_time = long(time.time())
		total_time = current_time - start_time

		title = ""
		body = ""
		need_freq_control = False
		is_error = False

		if error_status_ratio > error_status_ratio_threshold and total_time >= stats_interval:
			error_status_alert_details =  "Totally " + str(error_status_ratio*100) + "%" + "("+ str(total_error_count) + ")"\
			 + " queries has bad status " + monitor_words_list_str  + ", over "+ str(error_status_ratio_threshold*100) + "% " \
			 + " in surveillance time-window " + str(stats_interval) + " s"
			title = email_subject
			body = email_content + " -- " +  error_status_alert_details
			is_error = True
			self.set_cache_value_dynamic(monitor_item,'query_count',0)
			self.set_cache_value_dynamic(monitor_item,'error_count',0)
			self.set_cache_value_dynamic(monitor_item,'start_time', current_time)
		elif	total_time < stats_interval:			
			self.set_cache_value_dynamic(monitor_item,'query_count',total_query_count)
			self.set_cache_value_dynamic(monitor_item,'error_count', total_error_count)
		else:
			self.set_cache_value_dynamic(monitor_item,'query_count',0)
			self.set_cache_value_dynamic(monitor_item,'error_count',0)
			self.set_cache_value_dynamic(monitor_item,'start_time', current_time)


		if total_time>=stats_interval:
			need_freq_control = True
		
		if need_freq_control:
			self._freq_control.alert_control(monitor_item, is_error, stats_interval, title, body, True, True)



	def process_target_words_by_settings(self, monitor_item ,target_file_name, start_line_number, end_line_number):
		file_content = ""

		if end_line_number > 0:
			file_content = self.get_incremental_filecontent(target_file_name, start_line_number, end_line_number)
		else:
			file_content = self.get_incremental_filecontent_toend(target_file_name, start_line_number)
		
		#load config
		email_subject_base = self.conf.get(monitor_item,'email_subject')
		email_content_base = self.conf.get(monitor_item,'email_content')
		monitor_words_list = self.conf.get(monitor_item,'target_words').split(',')
		print monitor_words_list
		
		title = ""
		body = ""
		is_error = False
		need_freq_control = False

		for word in monitor_words_list:
			pattern = re.compile(word)
			if file_content.find(word) != -1:
				is_error = True
				size = str(len(pattern.findall(file_content)))
				print size
				pos = file_content.find(word)
				start_pos = (pos - 100)>0 and (pos - 100) or 0
				end_pos = (pos + 100) < len(file_content) and (pos + 100) or len(file_content) - 1

				log_content = file_content[start_pos:end_pos]
				print log_content
				email_subject = email_subject_base
				email_content = email_content_base + '  '+ ' 个数为：' + size+'\n' +log_content 				
				body = '[' + word + ']' + email_content
				title = '[' + word + ']' + email_subject

			else:
				is_error = False

			self._freq_control.alert_control(monitor_item+word, is_error, 300, title, body, True, True)
				

	def process_error_words_by_settings(self, target_files, monitor_words_list , start_line_number, end_line_number):
		
		words_count_list = []
		for index in range(0, len(monitor_words_list)):
			words_count_list.append(0)

		file_count = len(target_files)
		file_index = 0

		for file_path in target_files:
			if file_index == file_count -1:
				file_end = self.process_error_words_in_single_file(file_path, monitor_words_list, start_line_number, end_line_number, words_count_list)
			else:
				file_end = self.process_error_words_in_single_file(file_path, monitor_words_list, start_line_number, 0, words_count_list)

			start_line_number = 0
			file_index = file_index + 1
			

		return words_count_list

	def process_error_words_in_single_file(self, target_file_name, monitor_words_list , start_line_number, end_line_number, words_count_last_time_list):
		file_content = ""
		if end_line_number > 0:
			file_content = self.get_incremental_filecontent(target_file_name, start_line_number, end_line_number)				
		else:
			file_content = self.get_incremental_filecontent_toend(target_file_name, start_line_number)

		for index in range(0, len(monitor_words_list)):
			word = monitor_words_list[index]
			current_error_words_count = words_count_last_time_list[index]
			pattern = re.compile(word)
			result_list = pattern.findall(file_content)
			current_error_words_count = len(result_list) + current_error_words_count
			words_count_last_time_list[index] = current_error_words_count


	def process_overtime_by_settings(self, monitor_item ,target_file_list, start_line_number, end_line_number,  overtime_ratio_threshold, time_threshold):
		#load config					
		email_subject = self.conf.get(monitor_item,'email_subject')
		email_content = self.conf.get(monitor_item,'email_content')
		monitor_word = self.conf.get(monitor_item,'monitor_word')		
		time_format = self.conf.get(monitor_item,'time_format')		
		stats_interval = long(self.conf.get(monitor_item,'stats_interval'))
		request_time_unit = self.conf.get(monitor_item,'request_time_unit')
		time_cost_unit = self.conf.get(monitor_item,'time_cost_unit')

		#load cache
		start_time = 0l
		total_overtime_count = 0l
		total_query_count = 0l

		try:
			start_time = long(self.cache_conf.get(monitor_item,'start_time'))
			total_overtime_count = long(self.cache_conf.get(monitor_item,'overtime_count'))
			total_query_count = long(self.cache_conf.get(monitor_item,'query_count'))
		except Exception,e:
			print e


		log_stat = log_stats_for_time_module.logStat(self._log_type)
		log_stat.SetLogFilter(["SELECT"])
		log_stat.SetOverTimeThreshold(time_threshold)
		log_stat.SetTimeFormat(time_format)
		log_stat.SetLogRecordTimeSettings(request_time_unit, time_cost_unit)

		if 'csv' == self._log_type:
			request_time_index = int(self.conf.get(monitor_item,'request_time_index'))
			time_cost_index = int(self.conf.get(monitor_item,'time_cost_index'))
			log_stat.SetCSVLogSettings(request_time_index, time_cost_index)

		elif 'json' == self._log_type:
			request_time_key = self.conf.get(monitor_item,'request_time_key')
			time_cost_key = self.conf.get(monitor_item,'time_cost_key')	
			log_stat.SetJsonLogSettings(request_time_key, time_cost_key)

		elif 'regx' == self._log_type:
			log_regx =  self.conf.get(monitor_item,'log_regx')
			request_time_index = int(self.conf.get(monitor_item,'request_time_index'))
			time_cost_index = int(self.conf.get(monitor_item,'time_cost_index'))			
			log_stat.SetRegxLogSettings(log_regx, time_cost_index,request_time_index)


		file_index = 0
		file_count = len(target_file_list)

		for file in target_file_list:
			if (file_count -1)  == file_index:
				print file + "," + str(start_line_number)  + "," + str(end_line_number)
				file_end = log_stat.GrepFromTxtInFileByRange(file, monitor_word, start_line_number, end_line_number)
			else:
				print file + "," + str(start_line_number)  + "," + str(end_line_number)
				file_end = log_stat.GrepFromTxtInFileByRange(file, monitor_word, start_line_number, 0)

			start_line_number = 0
			file_index = file_index + 1

		over_time_query_count = log_stat.GetOvertimeCount() 
		query_count = log_stat.GetRequestCount()
		total_overtime_count += over_time_query_count
		total_query_count += query_count
		total_overtime_ratio = 0.0
		if total_query_count > 0:
			total_overtime_ratio = round(total_overtime_count*1.0/total_query_count, 2)

		print "over_time_query_count:" + str(over_time_query_count)
		print "total_overtime_ratio:" + str(total_overtime_ratio)

		current_time = long(time.time())
		total_time = current_time - start_time

		title = ""
		body = ""
		is_error = False
		need_freq_control = False

		if total_time >= stats_interval:
			need_freq_control = True
				
		if total_overtime_ratio > overtime_ratio_threshold and total_time >= stats_interval:
			over_time_details =  "Totally " + str(total_overtime_ratio*100) + "%" + "("+ str(total_overtime_count) + ")"\
			 + " queries exceed " + str(time_threshold) + " ms, " + "over "+ str(overtime_ratio_threshold*100) + "% " \
			 + " in surveillance time-window " + str(stats_interval) + " s"

			body = email_content + " --- " +  over_time_details
			title = email_subject
			is_error = True

			self.set_cache_value_dynamic(monitor_item,'query_count',0)
			self.set_cache_value_dynamic(monitor_item,'overtime_count',0)
			self.set_cache_value_dynamic(monitor_item,'start_time', current_time)
		elif	total_time < stats_interval:			
			self.set_cache_value_dynamic(monitor_item,'query_count',total_query_count)
			self.set_cache_value_dynamic(monitor_item,'overtime_count', total_overtime_count)
		else:
			self.set_cache_value_dynamic(monitor_item,'query_count',0)
			self.set_cache_value_dynamic(monitor_item,'overtime_count',0)
			self.set_cache_value_dynamic(monitor_item,'start_time', current_time)

		if need_freq_control:
			self._freq_control.alert_control(monitor_item, is_error, stats_interval, title, body, True, True)

	def process_single_file_error_status(self, filepath, keyword, error_code_patterns, start_line_number, end_line_number):
		print 'process_single_file_error_status'
		line_index = 0
		curfile = open(filepath)
		total_line_count = 0
		error_line_count = 0
		try:
			print "finding %s..." %(curfile)
			for line in curfile.readlines():
				line_index = line_index+1
				if line_index == end_line_number +1 and end_line_number > 0:
					break
				if line_index <= start_line_number:
					continue

				if keyword not in line:
					continue

				total_line_count = total_line_count + 1
				if self.match_multiple_world(error_code_patterns,line):
					error_line_count = error_line_count + 1

			print "process " + filepath + " end in line " + str(line_index)
			curfile.close()

		except Exception,ex:
			print Exception,":",ex
			self.record_error_message('process_single_file_error_status catch exception: ' + str(ex))
			
		finally:
			curfile.close()

		return (total_line_count, error_line_count)

	def match_multiple_world(self, words, line):
		hit = False
		for word in words:
			if word in line:
				hit = True
				break

		return hit

	def get_incremental_filecontent_toend(self, target_file_name, start_line_number):
		last_total = start_line_number
		cmd_total = 'wc -l ' + target_file_name + ' | awk \'{print $1}\''
		total = int(os.popen(cmd_total).read())		
		delta = int(total - last_total)		
		cmd_file_content = 'tail -' + str(delta) + ' '  + target_file_name
		file_content = os.popen(cmd_file_content).read()
		return file_content

	def get_incremental_filecontent(self, target_file_name, start_line_number, end_line_number):
		#sed -n '2,3p' leui_performance_2016-07-14_13:31:22.log
		last_total = start_line_number
		range_str = "'" + str(start_line_number) + "," + str(end_line_number) + "p'"
		cmd_file_content = "sed -n " + range_str + " " + target_file_name		
		file_content = os.popen(cmd_file_content).read()
		return file_content

	def get_increased_file_path_list(self, section_name):
		file_list = self.get_file_list()
		new_file_list = []

		start_line_number=0
		last_processed_file_name = ""
		last_processed_line_count = 0

		try:
			last_processed_file_name = self.cache_conf.get(section_name, 'last_file')
		except Exception,ex:
			print Exception,":",ex
		try:
			last_processed_line_count = int(self.cache_conf.get(section_name, 'lines'))
		except Exception,ex:
			print Exception,":",ex
				
		print "last_processed_file_name: " + last_processed_file_name + " from line:" + str(last_processed_line_count)
		
		if last_processed_file_name in file_list:
			hit_last_processed_file=False
			for index in range(0, len(file_list)):
				file_name = file_list[index]

				if file_name == last_processed_file_name:
					hit_last_processed_file = True;
					cmd_total = 'wc -l ' + file_name + ' | awk \'{print $1}\''
					total_line_count = int(os.popen(cmd_total).read())
					
					print file_name+" total_line_count "+ str(total_line_count)

					if total_line_count <= last_processed_line_count:
						continue

					start_line_number = last_processed_line_count
					
				if hit_last_processed_file == True:
					new_file_list.append(file_name)
		else:
			new_file_list = file_list
			
		return (new_file_list, start_line_number)

	def get_file_length(self, filepath):
		cmd_total = 'wc -l ' + filepath + ' | awk \'{print $1}\''
		total_line_count = int(os.popen(cmd_total).read())
		return total_line_count


	def ReadTargetRecordInFile(self, filepath, keyword, start_line_number, end_line_number, log_regx, log_paras_indice, log_paras_type, time_format,timestamp_unit):
		print 'ReadTargetRecordInFile'
		line_index = 0
		selected_lines = []
		curfile = open(filepath)
		total_record_lines_count = 0
		try:
			print "finding %s..." %(curfile)
			for line in curfile.readlines():
				line_index = line_index+1
				if line_index == end_line_number +1 and end_line_number > 0:
					break
				if line_index <= start_line_number:
					continue
				if keyword not in line:
					continue

				if 'json' == self._log_type:
					json_str = self.CreateJsonFromJsonLog(line, keyword, log_paras_type, time_format, timestamp_unit)
					selected_lines.append(json_str)
				elif 'csv' == self._log_type:
					json_str = self.CreateJsonFromCSVLog(line, log_paras_indice, log_paras_type, time_format, timestamp_unit)
					selected_lines.append(json_str)
				elif 'regx' == self._log_type:
					json_str = self.CreateJsonFromRegxLog(line, log_regx, log_paras_indice, log_paras_type, time_format, timestamp_unit)
					selected_lines.append(json_str)	

				total_record_lines_count += 1

			print "process " + filepath + " end in line " + str(line_index)
			curfile.close()

		except Exception,ex:
			print Exception,":",ex
			self.record_error_message('ReadTargetRecordInFile catch exception: ' + str(ex))
			
		finally:
			curfile.close()

		
		self.insert_db(selected_lines)
		return total_record_lines_count

	def CreateJsonFromJsonLog(self,line,keyword, log_paras_type, time_format,timestamp_unit):
		json_str = '{}'
		rate = 1
		if timestamp_unit == 'ms':
			rate = 1000

		if keyword in line:
			npos = line.find(keyword)
			if npos > 0 or '' == keyword :
				start_pos = line.find("{", npos)
				end_pos = line.rfind("}")
				if start_pos > 0 and end_pos > start_pos:
					json_str = line[start_pos : end_pos +1]
					for key in log_paras_type.keys():
						if "datetime" == log_paras_type[key]:		
							json_obj = json.loads(json_str)
							time_number_in_seconds = long(json_obj[key])/rate
							es_date = datetime.datetime.fromtimestamp(time_number_in_seconds)
							json_obj["datetime"] = es_date.isoformat()
							json_str = json.dumps(json_obj)
							break				
					
		return json_str
#[2016-09-21 22:48:29](7)(Thread: 0x00007f0b4afd5700): [audience_service::user2audience][COMMA],1474469309,2016-09-21 22:48:29,127.0.0.1,59020,127.0.0.1,/bigdata/audience_service/v0/user2audience?uid=31883222,31883222,,,56
#prefix,reqStartTime,reqStartTimeStrdirect_client_host,direct_client_port,real_client_host,server_mark,request_uri,uid,devide_id,device_type,response_time
	def CreateJsonFromCSVLog(self, line, log_paras, log_paras_type, time_format,timestamp_unit):
		
		rate = 1
		if timestamp_unit == 'ms':
			rate = 1000
		json_str = '{}'
		response_results = re.split('[,\n]', line)

		json_obj = {}
		for key in log_paras.keys():
			if "string" == log_paras_type[key]:
				json_obj[key] = response_results[log_paras[key]]
			if "int" == log_paras_type[key]:
				json_obj[key] = int(response_results[log_paras[key]])
			if "long" == log_paras_type[key]:
				json_obj[key] = long(response_results[log_paras[key]])
			if "datetime" ==  log_paras_type[key]:
				time_number_in_seconds = long(response_results[log_paras[key]])/rate
				es_date = datetime.datetime.fromtimestamp(time_number_in_seconds)
				json_obj["datetime"] = es_date.isoformat()
				json_obj[key] = long(response_results[log_paras[key]])
		
		json_str = json.dumps(json_obj)
		return json_str	

	def CreateJsonFromRegxLog(self, line, log_regx, log_paras_indice, log_paras_type, time_format, timestamp_unit):
		print 'CreateJsonFromRegxLog'
		rate = 1
		if timestamp_unit == 'ms':
			rate = 1000
		json_str = '{}'

		p = re.compile(log_regx)
		regx_matched = p.match(line)
		print regx_matched
		response_results = regx_matched.groups()

		print log_paras_indice
		print log_paras_type
		print response_results

		json_obj = {}
		for key in log_paras_indice.keys():
			if "string" == log_paras_type[key]:
				json_obj[key] = response_results[log_paras_indice[key]]
			if "int" == log_paras_type[key]:
				json_obj[key] = int(response_results[log_paras_indice[key]])
			if "long" == log_paras_type[key]:
				json_obj[key] = long(response_results[log_paras_indice[key]])
			if "datetime" ==  log_paras_type[key]:
				time_number_in_seconds = 0l
				if time_format!='number':
					time_number_in_seconds = time.mktime(time.strptime(response_results[log_paras_indice[key]], time_format))
				else:
					time_number_in_seconds = long(response_results[log_paras_indice[key]])/rate
				es_date = datetime.datetime.fromtimestamp(time_number_in_seconds)
				json_obj["datetime"] = es_date.isoformat()
				json_obj[key] = time_number_in_seconds
		
		json_str = json.dumps(json_obj)
		print json_str
		return json_str				

	def insert_db(self, doc_lines):
		es_hosts = self._target_log_db_uri.split(',')
		es = Elasticsearch(es_hosts)
		actions = []
		current_date_str = time.strftime("%Y-%m-%d", time.localtime(time.time())) 

		type_name = self._target_log_db_tablename
		if self._log_rotate:
			type_name = self._target_log_db_tablename + "_" +current_date_str

		for doc in doc_lines:
			action = {}
			action['_index'] = self._target_log_db_dbname
			action['_type'] = type_name
			action['_source'] = doc
			actions.append(action)

		helpers.bulk(es, actions) 


	def get_file_list(self):

		cmd = "ls -rt " + self._target_log_path + '/'+ self.log_name_prefix + '*'
		file_str = os.popen(cmd).read()
		file_list = file_str.split('\n')
		return file_list[0:len(file_list) - 1]


	def set_cache_value_dynamic(self,section,section_para_name, section_para_value):
		cfd = open(self._cache_path, 'w')
		if section not in self.cache_conf.sections():
			self.cache_conf.add_section(section)
		self.cache_conf.set(section, section_para_name, section_para_value)
		self.cache_conf.write(cfd)
		cfd.close()

	def send_curl_command(self,url):
		print url
		c = pycurl.Curl()
		c.setopt(c.URL, url)
		b = StringIO.StringIO()
		c.setopt(pycurl.WRITEFUNCTION,b.write)
		c.perform()
		c.close

	def record_error_message(self, error_message):

		today = datetime.datetime.today()
		try:
			log_prefix = 'monitor_error_log'
			date = today.strftime("%Y-%m-%d")
			filepath = self.cur_file_dir() + '/' + log_prefix + '_' + date + '.log'
			cmd = "echo " + error_message + " >> " + filepath
			os.popen(cmd)
		except Exception,e:
			print str(e)

	def cur_file_dir(self):
		#获取脚本路径
		path = sys.path[0]
		#判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
		if os.path.isdir(path):
			return path
		elif os.path.isfile(path):
			return os.path.dirname(path)


import getopt

def PrintHelp():
	print "-r/--directory= <target log folder path>"
	print "-c/--config= <config.ini> "
	print "--key= <monitor instance key, to identify different monitor process running in same machine> "

if __name__ == '__main__':

	print len(sys.argv)
	if len(sys.argv) <2 or sys.argv[1] == '-h':
		PrintHelp()
		exit(0)

	shortargs = 'c:r:1'
	longargs = ['directory=', 'config=', 'key=']
	opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs)   


	config_path =''
	cache_path = ''
	target_log_path = ''
	key = 'default'

	for opt, value in opts:
		if '-c' == opt:
			config_path = value
		if '-r' == opt:
			target_log_path = value  
		if '--config' == opt:
			config_path = value
		if '--directory' == opt:
			target_log_path = value
		if '--key' == opt:
			key = value

	print "config_path: " + config_path
	print "target_log_path: " + target_log_path
	print "key: " + key

	logMonitor.config_path=config_path
	logMonitor.target_log_path=target_log_path
	lm = logMonitor(config_path, cache_path, target_log_path, key )	
	lm.task_portal()