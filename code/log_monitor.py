#!/bin/python
#coding:UTF-8
'''
    @author:   verlink
    @desc:     log monitor 
    @date:     2015-6-16
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

class logMonitor():

    def __init__(self):

        self.conf = ConfigParser.ConfigParser()
        self.conf.read("/xxxx/dist/recommendation_service/bigdata_leui_full_logs/log_monitor.ini")
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
		            self.email_list = self.conf.get(item,'emails').split(';')
	    else:
		    if self.conf.get(item,'enable') != 'false':
			    monitor_list.append(item)
        for monitor_item in monitor_list:
                self.worker(monitor_item)

    def worker(self,monitor_item):
        
        if monitor_item == 'error_words_monitor':
            if self.conf.get(monitor_item,'monitor_words') == '':
                return
	    print 'error_words_monitor start'
            monitor_words_list = self.conf.get(monitor_item,'monitor_words').split(';')
	    threshold = self.conf.get(monitor_item,'threshold')
	    self.error_words_monitor(monitor_words_list,threshold)
	elif monitor_item == 'log_file_monitor':
	    print 'log_file_monitor start'
	    file_max_threshold = self.conf.get(monitor_item,'file_max_threshold')
	    self.log_file_monitor(file_max_threshold)
	elif monitor_item == 'target_words_monitor':
	    print 'target_words_monitor start'
	    monitor_words_list = self.conf.get(monitor_item,'target_words').split(';')
	    self.target_words_monitor(monitor_words_list)

        else:
            return 

    def log_name_everyday(self):

    	today = datetime.datetime.today()
	try:
		log_prefix = self.log_name.split('-')[0]
		date = today.strftime("%Y-%m-%d")
		self.log_name = log_prefix + '_' + date
	except Exception,e:
		print str(e)
		return

    def target_words_monitor(self,monitor_words_list):

	file_list = self.get_file_list()
	file_name = file_list[len(file_list) - 1]
	cmd_total = 'wc -l ' + file_name + ' | awk \'{print $1}\''
	total = int(os.popen(cmd_total).read())
	last_total = int(self.conf.get('target_words_monitor','static_number'))
	print last_total
	delta = int(total - last_total)
	cmd_file_content = 'tail -' + str(delta) + ' '  + file_name
	file_content = os.popen(cmd_file_content).read()
	for word in monitor_words_list:
		pattern = re.compile(word)
		if file_content.find(word) != -1:
			size = str(len(pattern.findall(file_content)))
			print size
			log_content = file_content[file_content.find(word):file_content.find(word) + 1000]
			email_subject = self.conf.get('target_words_monitor','email_subject')
			email_content = self.conf.get('target_words_monitor','email_content') + '  '+ ' 个数为：' + size+'\n' +log_content 
			self.set_conf_number_dynamic('target_words_monitor',total)
			self.alert_emails(email_subject,email_content)

    def get_file_list(self):

    	cmd = 'ls ' + self.log_name + '*'
	file_str = os.popen(cmd).read()
	file_list = file_str.split('\n')
	return file_list[0:len(file_list) - 1]

    def set_conf_number_dynamic(self,section,static_number):

	cfd = open('/xxxx/dist/recommendation_service/bigdata_leui_full_logs/log_monitor.ini','w')
    	self.conf.set(section,'static_number',static_number)
	self.conf.write(cfd)
	cfd.close()

    def error_words_monitor(self, monitor_words_list, threshold):

    	email_subject = self.conf.get('error_words_monitor','email_subject')
	email_content = self.conf.get('error_words_monitor','email_content')
	file_list = self.get_file_list()
	file_name = file_list[len(file_list) - 1]
	cmd_total = 'wc -l ' + file_name + ' | awk \'{print $1}\''
	total = int(os.popen(cmd_total).read())
	last_total = int(self.conf.get('error_words_monitor','static_number'))
	delta = int(total - last_total)
	cmd_file_content = 'tail -' + str(delta) + ' '  + file_name
	file_content = os.popen(cmd_file_content).read()
    	for word in monitor_words_list:
		pattern = re.compile(word)
		result_list = pattern.findall(file_content)
		if len(result_list) >= int(threshold):
			self.set_conf_number_dynamic('error_words_monitor',total)
			email_content = email_content + ' 阈值大小为:' + threshold + ' 错误词数量为:' + str(len(result_list))
			self.alert_emails(email_subject,email_content);

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

        monitor_str = ''
    	for monitor in self.email_list:
		monitor_str = monitor_str + ',' + monitor
	monitor_str = monitor_str[1:]
	email_content = urllib.quote(email_content)
	email_subject = urllib.quote(email_subject)
    	cmd_email = 'http://mailhttpapi/?receivers='+monitor_str+'&subject='+email_subject+'&content=' + email_content 
	self.send_curl_command(cmd_email)
	 

if __name__ == '__main__':

    lm = logMonitor()
    lm.task_portal()