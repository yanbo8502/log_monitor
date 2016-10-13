#!/usr/bin/env python
# -*- coding:utf-8 -*-
#./log_monitor.py ~/Codes/datamining_server_scripts/code/system_monitor/log_monitor.ini ~/Codes/dmp_letv_matrix_web/spring-boot-samples/catalina.base_IS_UNDEFINED/logs/dmp

'''
    @author:   yanbo
    @desc:     log monitor 
    @date:     2015-6-16
    @lastUpdate yanbo 2016-09-30
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

import sys
import random
import os
import time,datetime
import json
import urllib2 
import log_stats_for_time_module
import sys
import send_mail
import send_message

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

	def __init__(self, config_path, target_log_path):
		self._config_path = config_path
		self._target_log_path = target_log_path
		
		self.conf = ConfigParser.ConfigParser()
		self.conf.read(self._config_path)
		self.email_list = []
		self.log_name_prefix = ''
		self._log_type = self.conf.get('basic','log_type')

	def task_portal(self):
		section_list = self.conf.sections()
		monitor_list = []
		
		result = 0

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
		for monitor_item in monitor_list:
			try:
				self.worker(monitor_item)
				#raise Exception('test')
			except Exception,e:
				print str(e)
				error_message = monitor_item + 'catch exception: ' + str(e)
				print error_message
				self.record_error_message(error_message)


	def worker(self,monitor_item):

		#get scanning and processing settings and cached data of last scanning
		target_file_list, start_line_number = self.get_increased_file_path_list('basic')

		print target_file_list
		print start_line_number

		file_count = len(target_file_list)
		if file_count < 1:
			return

		last_file_path = target_file_list[file_count -1]

		end_line_number = self.get_file_length(last_file_path)
	
		if monitor_item == 'error_words_monitor':
			if self.conf.get(monitor_item,'monitor_words') == '':
				return
			print 'error_words_monitor start'
			self.error_words_monitor(target_file_list, start_line_number, end_line_number)
		elif monitor_item == 'target_words_monitor':
			print 'target_words_monitor start'
			self.target_words_monitor(target_file_list, start_line_number, end_line_number)
		elif monitor_item == 'user_request_monitor':
			print 'user_request_monitor start'
			self.log_query_record_monitor(target_file_list, start_line_number, end_line_number)
		elif monitor_item == 'overtime_monitor':
			print 'overtime_monitor start'
			self.overtime_monitor(target_file_list, start_line_number, end_line_number)
		else:
			return

		self.set_conf_value_dynamic("basic",'lines', end_line_number)
		self.set_conf_value_dynamic("basic",'last_file',last_file_path) 

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

		word_setting_str = self.conf.get('error_words_monitor','settings');
		word_settings = json.loads(word_setting_str)
		monitor_words_list = word_settings.keys()
		
		last_file_path= ""
	
		if len(target_file_list)!=0:

			#get scanning and processing settings and cached data of last scanning
			words_count_list = []
			words_count_thresholds = []
			#beginning scanning file content
			increased_words_count_list = self.process_error_words_by_settings(target_file_list, monitor_words_list, start_line_number, end_line_number)
	
			email_subject = self.conf.get('error_words_monitor','email_subject')
			email_content = self.conf.get('error_words_monitor','email_content')

			
			for index in range(0, len(monitor_words_list)):
				word = monitor_words_list[index]
				threshold = word_settings[word]['count_threshold']
				word_count = increased_words_count_list[index] + word_settings[word]['count']
				word_settings[word]['count'] = word_count
				start_time = word_settings[word]['start_time']
				current_time = long(time.time())
				total_time = current_time - long(start_time)
				stats_interval = word_settings[word]['stats_interval']

				#update by count
				if word_count >= int(threshold) and total_time>=stats_interval:
					
					start_time_str = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(start_time))
					 
					thisword_email_content =  email_subject + " " + email_content +  ' [' + word + ']' + ' threshold: ' + str(threshold) +\
					 ' exact count:' + str(word_count) + ' from ' + start_time_str + " within statistic period " + str(total_time) + " s"
					thisword_email_subject = email_subject + ' [' + word + ']'
					
					self._mail_handler.alert_emails(thisword_email_subject, thisword_email_content);
					self._message_handler.alert_phone_message(thisword_email_content);
					#mail is sent, reset status
					word_settings[word]['count'] = 0	

		for index in range(0, len(monitor_words_list)):
			word = monitor_words_list[index]
			
			#update by time
			stats_interval = word_settings[word]['stats_interval']
			start_time = word_settings[word]['start_time']
			current_time = long(time.time())

			if (current_time - start_time) > stats_interval:
				word_settings[word]['start_time'] = current_time
				word_settings[word]['count'] = 0

		#update config
		word_setting_str = json.dumps(word_settings)
		self.set_conf_value_dynamic("error_words_monitor",'settings',word_setting_str)
		

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

		log_paras = {}
		log_paras_type = {}
		timestamp_unit = 's'

		try:
			log_paras = eval(self.conf.get('user_request_monitor', 'log_paras'))
			log_paras_type = eval(self.conf.get('user_request_monitor', 'log_paras_type'))
			timestamp_unit = self.conf.get('user_request_monitor', 'timestamp_unit')
		except Exception,ex:
			print ex

		#get scanning and processing settings and cached data of last scanning
		file_index = 0
		file_count = len(target_file_list)

		for file_path in target_file_list:
			if file_index == file_count -1: 
				file_end = self.ReadTargetRecordInFile(file_path, keyword, start_line_number, end_line_number, log_paras, log_paras_type, timestamp_unit)
			else:
				file_end = self.ReadTargetRecordInFile(file_path, keyword, start_line_number, 0, log_paras, log_paras_type, timestamp_unit)
			file_index = file_index +1
			start_line_number = 0



	def process_target_words_by_settings(self, monitor_item ,target_file_name, start_line_number, end_line_number):
		file_content = ""

		if end_line_number > 0:
			file_content = self.get_incremental_filecontent(target_file_name, start_line_number, end_line_number)
		else:
			file_content = self.get_incremental_filecontent_toend(target_file_name, start_line_number)
		
		monitor_words_list = self.conf.get(monitor_item,'target_words').split(',')
		print monitor_words_list
		for word in monitor_words_list:
			pattern = re.compile(word)
			if file_content.find(word) != -1:
				size = str(len(pattern.findall(file_content)))
				print size
				pos = file_content.find(word)
				start_pos = (pos - 100)>0 and (pos - 100) or 0
				end_pos = (pos + 100) < len(file_content) and (pos + 100) or len(file_content) - 1

				log_content = file_content[start_pos:end_pos]
				print log_content
				email_subject = self.conf.get(monitor_item,'email_subject')
				email_content = self.conf.get(monitor_item,'email_content') + '  '+ ' 个数为：' + size+'\n' +log_content 				
				thisword_email_content = '[' + word + ']' + email_content
				thisword_email_subject = '[' + word + ']' + email_subject
				self._mail_handler.alert_emails(thisword_email_subject,thisword_email_content)
				self._message_handler.alert_phone_message(thisword_email_subject + " " + thisword_email_content)


	def process_error_words_by_settings(self, target_files, monitor_words_list , start_line_number, end_line_number):
		
		words_count_list = []
		for index in range(0, len(monitor_words_list)):
			words_count_list.append(0)

		end_line_number = 0
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
							
		email_subject = self.conf.get(monitor_item,'email_subject')
		email_content = self.conf.get(monitor_item,'email_content')
		monitor_word = self.conf.get(monitor_item,'monitor_word')
		
		time_format = self.conf.get(monitor_item,'time_format')
		start_time = long(self.conf.get(monitor_item,'start_time'))
		stats_interval = long(self.conf.get(monitor_item,'stats_interval'))
		total_overtime_count = long(self.conf.get(monitor_item,'overtime_count'))
		total_query_count = long(self.conf.get(monitor_item,'query_count'))
		request_time_unit = self.conf.get(monitor_item,'request_time_unit')
		time_cost_unit = self.conf.get(monitor_item,'time_cost_unit')

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

		
		file_index = 0
		file_count = len(target_file_list)
		for file in target_file_list:
			if (file_count -1)  == file_index:
				file_end = log_stat.GrepFromTxtInFileByRange(file, monitor_word, start_line_number, end_line_number)
			else:
				file_end = log_stat.GrepFromTxtInFileByRange(file, monitor_word, start_line_number, 0)

			start_line_number = 0
			file_index = file_index + 1

		over_time_query_count = log_stat.GetOvertimeCount() 
		query_count = log_stat.GetRequestCount()
		total_overtime_count += over_time_query_count
		total_query_count += query_count
		total_overtime_ratio = round(total_overtime_count*1.0/total_query_count, 2)
		print "over_time_query_count:" + str(over_time_query_count)
		print "total_overtime_ratio:" + str(total_overtime_ratio)

		current_time = long(time.time())
		total_time = current_time - start_time
				
		if total_overtime_ratio > overtime_ratio_threshold and total_time >= stats_interval:
			over_time_details =  "Totally " + str(total_overtime_ratio*100) + "%" + "("+ str(total_overtime_count) + ")" + " queries exceed time threshold " + str(time_threshold) + " ms in surveillance inerval " + str(stats_interval) + " s"
			email_content = email_content + " --- " +  over_time_details
			self._mail_handler.alert_emails(email_subject,email_content)
			self._message_handler.alert_phone_message(email_subject +" " + email_content)
			self.set_conf_value_dynamic(monitor_item,'query_count',0)
			self.set_conf_value_dynamic(monitor_item,'overtime_count',0)
			self.set_conf_value_dynamic(monitor_item,'start_time', current_time)
		elif	total_time < stats_interval:			
			self.set_conf_value_dynamic(monitor_item,'query_count',total_query_count)
			self.set_conf_value_dynamic(monitor_item,'overtime_count', total_overtime_count)
		else:
			self.set_conf_value_dynamic(monitor_item,'query_count',0)
			self.set_conf_value_dynamic(monitor_item,'overtime_count',0)
			self.set_conf_value_dynamic(monitor_item,'start_time', current_time)


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
		last_processed_file_name = self.conf.get(section_name, 'last_file')
		last_processed_line_count = int(self.conf.get(section_name, 'lines'))
		
		print "last_processed_file_name: " + last_processed_file_name
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


	def ReadTargetRecordInFile(self, filepath, keyword, start_line_number, end_line_number, log_paras, log_paras_type, timestamp_unit):
		print 'ReadTargetRecordInFile'
		line_index = 0
		selected_lines = []
		curfile = open(filepath)

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
					json_str = self.CreateJsonFromJsonLog(line, keyword, log_paras_type, timestamp_unit)
					selected_lines.append(json_str)
				elif 'csv' == self._log_type:
					json_str = self.CreateJsonFromCSVLog(line, keyword, log_paras, log_paras_type, timestamp_unit)
					selected_lines.append(json_str)
							

			print "process " + filepath + " end in line " + str(line_index)
			curfile.close()

		except Exception,ex:
			print Exception,":",ex
			self.record_error_message('ReadTargetRecordInFile catch exception: ' + str(ex))
			
		finally:
			curfile.close()

		
		self.insert_db(selected_lines)
		return line_index

	def CreateJsonFromJsonLog(self,line,keyword, log_paras_type, timestamp_unit):
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
					print json_str
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
	def CreateJsonFromCSVLog(self,line,keyword, log_paras, log_paras_type, timestamp_unit):
		
		rate = 1
		if timestamp_unit == 'ms':
			rate = 1000
		json_str = '{}'
		response_results = re.split('[,\n]', line)
		print log_paras
		print log_paras_type
		print response_results
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

	def insert_db(self, doc_lines):
		es_uri = "http://10.183.222.192:9200/letv_matrix_web_log/letv_matrix_web_user_request_record"
		for doc_line in doc_lines:
			if '{}' == doc_line:
				continue
			request = urllib2.Request(es_uri, doc_line)
			#request.add_header('Content-Type', 'application/json')
			#request.get_method = lambda:'PUT'           # 设置HTTP的访问方式
			request = urllib2.urlopen(request)


	def get_file_list(self):

		cmd = "ls -rt " + self._target_log_path + '/'+ self.log_name_prefix + '*'
		file_str = os.popen(cmd).read()
		file_list = file_str.split('\n')
		return file_list[0:len(file_list) - 1]


	def set_conf_value_dynamic(self,section,section_para_name, section_para_value):
		cfd = open(self._config_path,'w')
		self.conf.set(section, section_para_name, section_para_value)
		self.conf.write(cfd)
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


if __name__ == '__main__':

	print len(sys.argv)
	if len(sys.argv) <2 or sys.argv[1] == '-h':
		PrintHelp()
		exit(0)

	shortargs = 'c:r:1'
	longargs = ['directory=', 'config=']
	opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs)   
	print opts
	print args

	config_path =''
	target_log_path = ''

	for opt, value in opts:
		if '-c' == opt:
			config_path = value
		if '-r' == opt:
			target_log_path = value  
		if '--config' == opt:
			config_path = value
		if '--directory' == opt:
			target_log_path = value

	print "config_path: " + config_path
	print "target_log_path: " + target_log_path

	logMonitor.config_path=config_path
	logMonitor.target_log_path=target_log_path
	lm = logMonitor(config_path,target_log_path )	
	lm.task_portal()
