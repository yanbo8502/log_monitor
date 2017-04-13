#!/usr/bin/env python
#  -*- coding:utf-8 -*-
############
# 
# 
# 遍历文件夹或者文件的日志中的关键字，以便提取时间字符串，转化为数字，进行统计
############
#python log_stats_for_time.py -t csv -c comma_log.ini -k GetUserDeviceAudience -f /home/yanbo/Codes/dmp_data_server_with_libevent/code/builder/log_performance/libevent_http_performance_2016-09-19_21:43:41.log
# import module
import os
import sys
import cmd
import string
import time
import json
import getopt
import log_stats_for_time_module
import ConfigParser

def PrintHelp():
    print "-h for help"
    print "-f <target file path>"
    print "-r/--directory= <target folder path>"
    print "-t/--log_type= <log type> \'custom\' , \'json\',\'regx\',\'csv\', \'custom\' is for user customized-development support"
    print "-k/--keyword= <line filter keyword>, only lines containning this keyword will be involved"
    print "--time_threshold= <over time threhold>"
    print "--pattern= <file name fiter pattern>, keyword or postfix in log file name "
    print "--time_pattern= <log time-stamp fiter pattern>, use given time-stamp string segement like \'2016-09:01 21:15\'  to filter log within certain minute/hour/day "
    print "-c/--log_conf= <log config file path>,  for complicated-format requiring regx to parse, or some csv-format logs, some settings is not convenient to input by command line"
    print "--time_format= <date time format, for time parsing>, default is %Y-%m-%d %H:%M:%S, use \'number\' for decimal timestamp like 14569793275"
    print "--time_cost_unit= <unit for response time number>, \'ms\' or \'s\' default is \'ms\' "
    print "--request_time_unit	= <unit for log time stamp>, \'ms\' or \'s\' default is \'s\', python time methon default is \'s\' "
    print "--request_time_index= <index number  for splitted array of one log line>,  0,1,2 ~, used for comma-delimited log, value index of request log time stamp "
    print "--time_cost_index= <index number for splitted array of one log line >,  0,1,2 ~, used for comma-delimited log, value index of response time cost "
    print "--request_time_key= <json key name>,  used for json log, value key of request log time stamp "
    print "--time_cost_key= <json key name>,  used for json log, value key of response time cost "

if __name__=="__main__":


    print len(sys.argv)
    if sys.argv[1] == '-h':
        PrintHelp()
        exit(0)

    shortargs = 'c:f:r:k:t:1'
    longargs = ['directory=', 'keyword=', 'time_threshold=', "pattern=", 
    "log_type=", 'print', 'time_pattern=', 'time_format=', 'log_conf=', 
    'request_time_index=', 'time_cost_index=', 'time_cost_unit=', 'request_time_unit	=',
    'request_time_key=', 'time_cost_key=']
    opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs)   
    print opts
    print args
    time_format = "%Y-%m-%d %H:%M:%S"
    log_type =''
    keyword = ''
    mode = "file"
    overtime_threshold= 0;
    filepath = ""
    file_pattern = ""
    print_log_detail = False
    time_pattern = ""
    log_conf_path = ""
    time_cost_index = -1
    request_time_index = -1
    time_cost_unit='ms'
    request_time_unit	='s'
    request_time_key = ""
    time_cost_key = ""

    for opt, value in opts:
        if '-f' == opt:
            filepath = value
            mode = 'file'
        if '-r' == opt:
            filepath = value  
            mode = 'directory' 
        if '-k' == opt:
            keyword = value
        if '-t' == opt:
            log_type = value
        if '--log_type' == opt:
            log_type = value
        if '--directory' == opt:
            filepath = value
        if '--keyword' == opt:
            keyword = value
        if '--time_threshold' ==opt:
            overtime_threshold = int(value)
        if '--pattern' == opt:
            file_pattern = value
        if '--print' == opt:
            print_log_detail = True
        if '--time_pattern' == opt:
            time_pattern = value
        if '--log_conf' == opt:
            log_conf_path = value
        if '-c' == opt:
            log_conf_path = value
        if '--time_format' == opt:
            time_format = value
        if '--time_cost_index' == opt:
            time_cost_index = int(value)
        if '--request_time_index' == opt:
            request_time_index = int(value)
        if '--time_cost_unit'==opt:
            time_cost_unit = value
        if '--request_time_unit	'==opt:
            request_time_unit	 = value
        if '--time_cost_key' == opt:
            time_cost_key = value
        if '--request_time_key' == opt:
            request_time_key = value

    print "keyword: " + keyword
    print "mode: " + mode
    print "log_type: " + log_type
    print "overtime_threshold: " + str(overtime_threshold)
    print "file_pattern: " + file_pattern
    print "filepath: " + filepath
    print "print_log_detail: " + str(print_log_detail)
    print "time_pattern: " + time_pattern
    print "time_format: " + time_format
    print "time_cost_index: " + str(time_cost_index)
    print "request_time_index: " + str(request_time_index)
    print "time_cost_key: " + str(time_cost_key)
    print "request_time_key: " + str(request_time_key)
    print "time_cost_unit: " + str(time_cost_unit)
    print "request_time_unit	: " + str(request_time_unit	)

    if mode == '' or log_type == '' or filepath == '':
        print 'missing necessary arguments.'
        PrintHelp()
        exit(1)
    
    start_time =  time.time()
  

    log_stat = log_stats_for_time_module.logStat(log_type)
    log_stat.SetLogFilter(["SELECT"])
    log_stat.SetTimePattern(time_pattern)

    if log_conf_path!="":
        conf = ConfigParser.ConfigParser()
        conf.read(log_conf_path)
        try:
            time_format = conf.get("basic",'time_format')
        except Exception,e:
                print str(e)
 
        try:
            request_time_index =  int(conf.get("basic",'request_time_index'))
        except Exception,e:
                print str(e) 

        try:
            time_cost_index = int(conf.get("basic",'time_cost_index'))
        except Exception,e:
                print str(e) 

        try:
            log_rex_str = conf.get("basic",'log_regx')
        except Exception,e:
                print str(e)      
        
        try:
            time_cost_unit = conf.get("basic",'time_cost_unit')
        except Exception,e:
                print str(e) 

        try:
            request_time_unit	 = conf.get("basic",'request_time_unit	')
        except Exception,e:
                print str(e)

        try:
            request_time_key =  conf.get("basic",'request_time_key')
        except Exception,e:
                print str(e) 

        try:
            time_cost_key = conf.get("basic",'time_cost_key')
        except Exception,e:
                print str(e) 


    if log_type == "regx":
        if log_conf_path == "":
            print 'regx format need log config'
            PrintHelp()
            exit(1)
            
        log_stat.SetRegxLogSettings(log_rex_str, time_cost_index, request_time_index)
        print "log_rex_str " + log_rex_str

    if log_type == "csv":
        if request_time_index <0 or time_cost_index <0:
            print 'missing request_time_index or time_cost_index for csv log, use command-arg or same property name in .ini'
            PrintHelp()
            exit(1)

        log_stat.SetCSVLogSettings(request_time_index,time_cost_index)

    if log_type == "json":
        if request_time_key == '' or time_cost_key == '':
            print 'missing request_time_key or time_cost_key for json log, use command-arg or same property name in .ini'
            PrintHelp()
            exit(1)

        log_stat.SetJsonLogSettings(request_time_key,time_cost_key)

    log_stat.SetTimeFormat(time_format)
    log_stat.SetLogRecordTimeSettings(request_time_unit	, time_cost_unit)

    if overtime_threshold > 0:
        log_stat.SetOverTimeThreshold(overtime_threshold)
    if mode == 'directory':
        if file_pattern == "":
            log_stat.GrepFromTxtInFolder(filepath, keyword)
        else:
            log_stat.GrepFromTxtInFolderByPattern(filepath, file_pattern, keyword)
    elif mode == "file":
        log_stat.GrepFromTxtInFile(filepath, keyword)
    else:
        print "invalid mode"
    #print output
    stats_threshold_array=[0,50,100,300, 500,1000, 3000]
    log_stat.SetValueStatsThresholds(stats_threshold_array)
    log_stat.StatSummary()
    log_stat.StatsByTimeRanges()
    log_stat.StatsByFixedRatios()

    log_stat.PrintSummaryStats()
    log_stat.PrintFixedRatiosStats()
    log_stat.PrintTimeRangeStats()


    end_time =  time.time()
    duration = end_time - start_time

    print "time cost:"
    print duration
    
    if overtime_threshold > 0:
        print '在处理范围内，超时的请求个数为' + str(log_stat.GetOvertimeCount())
        if print_log_detail:
            log_stat.PrintOvertimeLogs()
