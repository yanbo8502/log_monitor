#!/usr/bin/env python
#coding:UTF-8

'''
    @author:   verlink, yanbo
    @desc:     log monitor 
    @date:     2015-6-16
    @lastUpdate yanbo 2015-12-18
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

class logMonitor():
	config_path = ""
	target_log_path = ""
	def __init__(self):
		print self.config_path
		self.conf = ConfigParser.ConfigParser()
		self.conf.read(self.config_path)
		self.email_list = []
		self.log_name = ''


	def task_portal(self):
		section_list = self.conf.sections()
		monitor_list = []
		email_list = []
		result = 0

		for item in section_list:
			if item == 'basic':
				if self.conf.get(item,'enable') == 'false':
					return
				else:
					self.log_name = self.conf.get(item,'log_name')
					self.log_name_everyday()
					self.email_list = self.conf.get(item,'emails').split(',')
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
	
		if monitor_item == 'error_words_monitor':
			if self.conf.get(monitor_item,'monitor_words') == '':
				return
			print 'error_words_monitor start'
			monitor_words_list = self.conf.get(monitor_item,'monitor_words').split(',')
			threshold = self.conf.get(monitor_item,'threshold')
			self.error_words_monitor(monitor_words_list,threshold)
		elif monitor_item == 'log_file_monitor':
			print 'log_file_monitor start'
			file_max_threshold = self.conf.get(monitor_item,'file_max_threshold')
			self.log_file_monitor(file_max_threshold)
		elif monitor_item == 'target_words_monitor':
			print 'target_words_monitor start'
			monitor_words_list = self.conf.get(monitor_item,'target_words').split(',')
			self.target_words_monitor(monitor_words_list)
		elif monitor_item == 'user_request_monitor':
			print 'user_request_monitor start'
			monitor_words_list = self.conf.get(monitor_item,'target_words').split(',')
			self.log_query_record_monitor(monitor_words_list)

		else:
			return 

	def log_name_everyday(self):

		today = datetime.datetime.today()
		try:
			log_prefix = self.log_name.split('-')[0]
			date = today.strftime("%Y-%m-%d")
			self.log_name = log_prefix + '-' + date
			print self.log_name
		except Exception,e:
			print str(e)
			return

	def target_words_monitor(self,monitor_words_list):
	
		#get scanning and processing settings and cached data of last scanning
		target_file_name, start_line_number = self.get_target_file_path('target_words_monitor')

		print target_file_name
		print start_line_number

		#beginning scanning file content
		end_line_number = self.process_target_words_by_settings('target_words_monitor', target_file_name, start_line_number)
		
		#update config
		self.set_conf_value_dynamic("target_words_monitor",'lines',end_line_number)
		self.set_conf_value_dynamic("target_words_monitor",'last_file',target_file_name)

	def process_target_words_by_settings(self, monitor_item ,target_file_name, start_line_number):

		file_content, end_line_number= self.get_incremental_filecontent(target_file_name, start_line_number)
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
				self.alert_emails(thisword_email_subject,thisword_email_content)

		return end_line_number

	def error_words_monitor(self, monitor_words_list, threshold):

		target_file_name, start_line_number = self.get_target_file_path('error_words_monitor')

		print target_file_name
		print start_line_number

		#get scanning and processing settings and cached data of last scanning
		error_words_count_last_time_str_list = self.conf.get('error_words_monitor','static_number').split(',')
		
		words_count_last_time_list = []
		words_count_thresholds = []
		self.get_settings_for_each_word('error_words_monitor', monitor_words_list, words_count_last_time_list, words_count_thresholds)
		
		print words_count_last_time_list
		print words_count_thresholds		

		
		#beginning scanning file content
		end_line_number = self.process_error_words_by_settings('error_words_monitor', target_file_name, start_line_number, words_count_last_time_list, words_count_thresholds)
		print words_count_last_time_list

		#update config
		error_words_count_last_time_list_str = ""
		for index in range(0, len(words_count_last_time_list)):
			word_count = words_count_last_time_list[index]
			if index > 0:
				error_words_count_last_time_list_str = error_words_count_last_time_list_str + ','
			error_words_count_last_time_list_str  = error_words_count_last_time_list_str + str(word_count)

		self.set_conf_value_dynamic("error_words_monitor",'lines',end_line_number)
		self.set_conf_value_dynamic("error_words_monitor",'last_file',target_file_name)
		self.set_conf_value_dynamic("error_words_monitor",'static_number',error_words_count_last_time_list_str)

	def process_error_words_by_settings(self, monitor_item ,target_file_name, start_line_number, words_count_last_time_list, words_count_thresholds):
		file_content, end_line_number= self.get_incremental_filecontent(target_file_name, start_line_number)		
		
		email_subject = self.conf.get(monitor_item,'email_subject')
		email_content = self.conf.get(monitor_item,'email_content')
		monitor_words_list = self.conf.get(monitor_item,'monitor_words').split(',')
		
		for index in range(0, len(monitor_words_list)):
			word = monitor_words_list[index]
			current_error_words_count = words_count_last_time_list[index]
			pattern = re.compile(word)
			result_list = pattern.findall(file_content)
			current_error_words_count = len(result_list) + current_error_words_count
			words_count_last_time_list[index] = current_error_words_count
			threshold = words_count_thresholds[index]
			if current_error_words_count >= int(threshold):
				thisword_email_content = email_content+ '[' + word + ']' + ' 阈值大小为:' + str(threshold) + ' 错误词数量为:' + str(current_error_words_count)
				thisword_email_subject = email_subject + '[' + word + ']'
				print thisword_email_content
				self.alert_emails(thisword_email_subject, thisword_email_content);
				#mail is sent, reset status
				words_count_last_time_list[index] = 0

		return end_line_number

	#thresholds and last_accumulated_counts for each word
	def get_settings_for_each_word(self, monitor_item, monitor_words_list, words_count_last_time_list, words_count_thresholds):
		error_words_count_last_time_str_list = self.conf.get(monitor_item,'static_number').split(',')		
		
		for index in range(0, len(monitor_words_list)):
			words_count_last_time_list.append(0)

		for index in range(0, len(error_words_count_last_time_str_list)):
			words_count_last_time_list[index] = int(error_words_count_last_time_str_list[index])

		error_words_count_threshold_strs = self.conf.get(monitor_item,'threshold').split(',')	
		for index in range(0, len(error_words_count_threshold_strs)):
			words_count_thresholds.append(int(error_words_count_threshold_strs[index]))


	def get_incremental_filecontent(self, target_file_name, start_line_number):
		last_total = start_line_number
		cmd_total = 'wc -l ' + target_file_name + ' | awk \'{print $1}\''
		total = int(os.popen(cmd_total).read())		
		delta = int(total - last_total)		
		cmd_file_content = 'tail -' + str(delta) + ' '  + target_file_name
		file_content = os.popen(cmd_file_content).read()
		return (file_content, total)

	def get_target_file_path(self, section_name):
		file_list = self.get_file_list()
		
		target_file_name = file_list[len(file_list) - 1]

		start_line_number=0
		last_processed_file_name = self.conf.get(section_name, 'last_file')
		last_processed_line_count = int(self.conf.get(section_name, 'lines'))
		
		print last_processed_file_name
		
		hit_last_processed_file=False
		for index in range(0, len(file_list)):
			file_name = file_list[index]
			if file_name == last_processed_file_name:
				hit_last_processed_file = True;
				cmd_total = 'wc -l ' + file_name + ' | awk \'{print $1}\''
				total_line_count = int(os.popen(cmd_total).read())
				
				print file_name+" total_line_count "+ str(total_line_count)
				if total_line_count == last_processed_line_count and index < len(file_list) -1:
					continue
				target_file_name = file_name
				start_line_number = last_processed_line_count
				break
			if hit_last_processed_file == True:
				target_file_name = file_name
				break
		return (target_file_name, start_line_number)

	def log_query_record_monitor(self,monitor_words_list):
		print monitor_words_list
		
		target_file_name, start_line_number = self.get_target_file_path('user_request_monitor')
		keyword = monitor_words_list[0]

		print target_file_name
		print keyword
		print start_line_number
		self.ReadTargetRecordInFile(target_file_name, keyword, start_line_number)

	def ReadTargetRecordInFile(self, filepath, keyword, start_line_number):
		print 'ReadTargetRecordInFile'
		line_index = 0
		selected_lines = []
		curfile = open(filepath)

		try:
			print "finding %s..." %(curfile)
			for line in curfile.readlines():
				line_index = line_index+1
				if line_index <= start_line_number:
					continue

				if keyword in line:
					npos = line.find(keyword)
					if npos > 0:
						start_pos = line.find("{", npos)
						end_pos = line.rfind("}")
						if start_pos > 0 and end_pos > start_pos:
							record = line[start_pos : end_pos +1]						
							selected_lines.append(record)
							

			print "process " + filepath + " end in line " + str(line_index)
			self.set_conf_value_dynamic("user_request_monitor",'lines',line_index)
			self.set_conf_value_dynamic("user_request_monitor",'last_file',filepath)
			curfile.close()

		except Exception,ex:
			print Exception,":",ex
			self.record_error_message('ReadTargetRecordInFile catch exception: ' + str(ex))
			
		finally:
			curfile.close()

		
		self.insert_db(selected_lines)

	def insert_db(self, doc_lines):
		es_uri = "http://localhost:9200/es_index/es_type"
		for doc_line in doc_lines:
			print doc_line			
			record_doc = json.loads(doc_line)
			#self.insert_es(record_doc, es_uri)

	def insert_es(self, doc, es_uri):
		#{"cliIP":"127.0.0.1","logDate":"2015-12-18","reqProcTime":28,"reqStartTimeStr":"2015-12-18 15:05:54.188","serIP":"127.0.0.1","srcName":"生态概览-乐视网-数据","userAgent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0","userName":"yanbo"}		
		es_doc = {}
		time_number_in_seconds = int(doc["reqStartTime"]/1000)
		es_date = datetime.datetime.fromtimestamp(time_number_in_seconds)
		print es_date
		es_doc["datetime"] = es_date.isoformat()
		es_doc["client_ip"] = doc["cliIP"]
		es_doc["date"] = doc["logDate"]
		es_doc["time"] = doc["reqStartTime"]
		es_doc["process_time"] = int(doc["reqProcTime"])
		es_doc["request_datetime"] = doc["reqStartTimeStr"]
		es_doc["server_ip"] = doc["serIP"]
		es_doc["requested_source"] = doc["srcName"]
		es_doc["useragent"] = doc["userAgent"]
		es_doc["username"] = doc["userName"]
		log_date = doc["logDate"]
		
		jdata = json.dumps(es_doc) 
		print jdata
		request = urllib2.Request(es_uri, jdata)
		#request.add_header('Content-Type', 'application/json')
		#request.get_method = lambda:'PUT'           # 设置HTTP的访问方式
		request = urllib2.urlopen(request)

	def get_file_list(self):

		cmd = "ls -rt " + self.target_log_path + '/'+ self.log_name + '*'
		file_str = os.popen(cmd).read()
		file_list = file_str.split('\n')
		return file_list[0:len(file_list) - 1]


	def set_conf_value_dynamic(self,section,section_para_name, section_para_value):
		print self.config_path
		cfd = open(self.config_path,'w')
		self.conf.set(section, section_para_name, section_para_value)
		self.conf.write(cfd)
		cfd.close()


	def log_file_monitor(self,file_max_threshold):

		email_subject = self.conf.get('log_file_monitor','email_subject')
		email_content = self.conf.get('log_file_monitor','email_content')
		file_list = self.get_file_list()
		file_name = file_list[len(file_list) - 1]
		cmd = "ls -rt " + file_name + " | awk '{print $5}'"
		file_size = os.popen(cmd).read()
		if int(file_size.strip()) >= int(file_max_threshold):
			self.alert_emails(email_subject,email_content)

	def send_curl_command(self,url):

		c = pycurl.Curl()
		c.setopt(c.URL, url)
		b = StringIO.StringIO()
		c.setopt(pycurl.WRITEFUNCTION,b.write)
		c.perform()
		c.close

	def alert_emails(self,email_subject,email_content):
		#记录报警时间
		check_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time())) + '---'
		print check_time
		#check_time=''

		monitor_str = ''
		for monitor in self.email_list:
			monitor_str = monitor_str + ',' + monitor

		monitor_str = monitor_str[1:]
		email_content = urllib.quote(check_time + email_content)
		email_subject = urllib.quote(email_subject)
		cmd_email = 'http://http_mail_server/mailer/send/?receivers='+monitor_str+'&subject='+email_subject+'&content=' + email_content 
		self.send_curl_command(cmd_email)

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


if __name__ == '__main__':
	logMonitor.config_path=sys.argv[1]
	logMonitor.target_log_path=sys.argv[2]
	lm = logMonitor()	
	lm.task_portal()
