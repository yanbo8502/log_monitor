#!/usr/bin/env python
#  -*- coding:utf-8 -*-
############
# 
# 
# 遍历文件夹或者文件的日志中的关键字，以便提取时间字符串，转化为数字，进行统计
############

# import module
import os
import sys
import cmd
import string
import time
import json
import getopt
import ConfigParser
import re
import math

#2016-05-10 13:34:49
# grep keyword from txt type file only
class logStat():
    _log_mode = ""
    total_time_range = 0.0
    query_time_array = []
    overtime_array = []
    value_stats_thresholds = []
    output_stats = []
    output_stats_ratio = []
    filter_words = []
    overtime_threshold = 1000
    _time_pattern = ""
    _nginx_log_rex_str = ""
    _nginx_timecost_index = 0
    _nginx_date_index = 0
    _ratio_stats = []
    stats_ratios = [0.5, 0.9, 0.95, 0.99, 0.999, 0.9999, 1.0]
    _total_log_start_time = 0l
    _total_log_end_time = 0l
    _avg_time_in_ms_per_request = 0.0
    _std_time_in_ms = 0.0
    _comma_log_response_time_cost_index = 0
    _comma_log_request_time_index = 0
    _timestamp_format = '%Y-%m-%d %H:%M:%S'
    _record_time_unit = 'ms'
    _time_cost_unit = 'ms'
    _json_time_cost_key = ""
    _json_request_time_key = ""

    def __init__(self, log_mode):
        self._log_mode = log_mode

    def SetLogRecordTimeSettings(self, record_time_unit, time_cost_unit):
        if ''!=record_time_unit:
            self._record_time_unit = record_time_unit
        if ''!=time_cost_unit:
            self._time_cost_unit = time_cost_unit

    def SetNginxLogSettings(self,  nginx_log_rex_str, nginx_timecost_index, nginx_date_index):
        self._nginx_log_rex_str = nginx_log_rex_str
        self._nginx_timecost_index = nginx_timecost_index
        self._nginx_date_index = nginx_date_index

    def SetCSVLogSettings(self, time_start_index, time_cost_index):
        self._comma_log_response_time_cost_index = time_cost_index
        self._comma_log_request_time_index = time_start_index

    def SetJsonLogSettings(self, request_time_key, time_cost_key):
        self._json_request_time_key = request_time_key
        self._json_time_cost_key = time_cost_key

    def SetTimeFormat(self, time_format):
        if ''!=time_format:
            self._timestamp_format = time_format

    def SetTimePattern(self, time_pattern):
        self._time_pattern = time_pattern

    def SetLogFilter(self, filter_words):
        self.filter_words = filter_words

    def SetOverTimeThreshold(self, time_thr):
        self.overtime_threshold = time_thr

    def SetValueStatsThresholds(self, _value_stats_thresholds):
        self.value_stats_thresholds = _value_stats_thresholds

    def SetQueryTimes(self, query_times):
        self.query_time_array = query_times

    def SetTotalTime(self, total_time):
        self.total_time_range = total_time

    def GetRequestCount(self):
        return len(self.query_time_array)

    def GetTimeStats(self):
        return self.output_stats

    def GetTimeStatsRatio(self):
        total_query_count = len(self.query_time_array)
        self.output_stats_ratio = []
        for count in self.output_stats:
            self.output_stats_ratio.append(round(count*1.0/total_query_count, 4))
        return self.output_stats_ratio

    def GetAllQueryTimes(self):
        return self.query_time_array

    def GetTotalTimeForAllRequests(self):
        return self.total_time_range

    def ExtractDateTimeFromLog(self, line):
        if 'custom' == self._log_mode:
            return self.ExtractDateTimeFromCustomLog(line)
        if 'nginx' == self._log_mode:
            return self.ExtractDateTimeFromNginxLog(line)
        if 'json'  ==  self._log_mode:
            return self.ExtractDateTimeFromJsonLog(line)
        if 'csv'  ==  self._log_mode:
            return self.ExtractDateTimeFromCSVLog(line)
        # todo support json log

    def ExtractDateTimeFromCustomLog(self, line):
        time_value = 0l
        try:
            time_str = ""
            start_pos = line.find("[")
            end_pos = line.find("]")
            if start_pos >= 0 and end_pos > start_pos:
                time_str = line[start_pos + 1 : end_pos]
            print time_str 
            #python time is in unit second
            time_value = time.mktime(time.strptime(time_str,self._timestamp_format))
        except Exception,ex:
            print Exception,":",ex
   
            #raise ex 
        #finally:
            
        return time_value

    def ExtractDateTimeFromNginxLog(self, line):
        time_value = 0l
        try:
            p = re.compile(self._nginx_log_rex_str)
            print p.match(line).groups()
            request_date_str = p.match(line).group(self._nginx_date_index)
            print request_date_str
            #'29/Jul/2016:16:01:15
            time_value = time.mktime(time.strptime(request_date_str,'%d/%b/%Y:%H:%M:%S'))
            print time_value
        except Exception,ex:
            print Exception,":",ex
            #raise ex 
        #finally:
            
        return time_value

    def ExtractDateTimeFromCSVLog(self, line):
        time_rate = 1
        if 'ms' == self._record_time_unit:
            time_rate = 1000

        response_results = re.split('[,\n]', line)
        request_time = 0
        print self._timestamp_format
        print response_results
        print "ExtractDateTimeFromCSVLog"
        if "number" == self._timestamp_format:
            request_time = int(response_results[self._comma_log_request_time_index])/time_rate
        else:
            request_date_str = response_results[self._comma_log_request_time_index]
            request_time = time.mktime(time.strptime(request_date_str, self._timestamp_format))
        return request_time

    def ExtractDateTimeFromJsonLog(self, line):
        #performance line format is  {"xxx":"xxxx", ..., "reqProcTime":123,....}
        request_time = -1
        time_rate = 1
        if 'ms' == self._record_time_unit:
            time_rate = 1000

        start_pos = line.find("{")
        end_pos = line.rfind("}")
        if start_pos >= 0 and end_pos > start_pos:
            record = line[start_pos : end_pos +1]                       
            record_doc = json.loads(record)
            if self._json_request_time_key in record_doc.keys():
                if "number" == self._timestamp_format:
                    request_time = int(record_doc[self._json_request_time_key])/time_rate
                else:
                    request_date_str = record_doc[self._json_request_time_key]
                    request_time = time.mktime(time.strptime(request_date_str, self._timestamp_format))


        return request_time

    def parseLineForPerformanceInNginxFormat(self, line, keyword):
        #performance line format is  xxxx keyword: 123ms xxxxx
        target_time = -1

        if keyword in line:

            p = re.compile(self._nginx_log_rex_str)
            line = line.strip("\n")
            try:
                request_timecost_str = p.match(line).group(self._nginx_timecost_index)
            except Exception as e:
                print line
                raise e
            #original unit is seconds
            target_time = float(request_timecost_str)*1000

        return target_time

    def parseLineForPerformanceInCustomFormat(self, line, keyword):
        #performance line format is  xxxx keyword: 123ms xxxxx
        target_time = -1
        if keyword in line:
            npos = line.find("ms")
            if npos > 0:
                tabpos = line.rfind(" ", 0, npos)
            if tabpos > 0:
                time_in_milli = line[tabpos+1 : npos]
                time_in_milli_number = string.atoi(time_in_milli)
                target_time = time_in_milli_number
        return target_time

    def parseLineForPerformanceInJsonFormat(self, line, keyword):
       
        time_rate = 1000
        if 'ms' == self._time_cost_unit:
            time_rate = 1
        response_time = -1
        if keyword in line:
            npos = line.find(keyword)
            if npos > 0 or keyword == "":
                start_pos = line.find("{", npos)
                end_pos = line.rfind("}")
                if start_pos >= 0 and end_pos > start_pos:
                    record = line[start_pos : end_pos +1]                       
                    record_doc = json.loads(record)
                    if self._json_time_cost_key in record_doc.keys():
                        response_time = int(record_doc[self._json_time_cost_key])*time_rate
        return response_time


    def parseLineFroPerformanceInCSVFormat(self, line):
        time_cost = 0;
        response_results = re.split('[,\n]', line)

        if len(response_results) > self._comma_log_response_time_cost_index:
            time_cost = int(response_results[self._comma_log_response_time_cost_index])
        return time_cost

    def IsValid(self, line, filter_words):
        for word in filter_words:
            if word in line:
                return False
        return True

    def GrepFromTxtInFile(self, filepath, keyword):
        return self.GrepFromTxtInFileByRange(filepath, keyword, 1)
        

    def GrepFromTxtInFileByRange(self, filepath, keyword, start_line):
        first_query = ""

        curfile = open(filepath)
        print "finding %s..." %(curfile)
        lines = curfile.readlines()
        line_index = 0
        for line in lines:

            line_index = line_index + 1

            if line_index < start_line:
                continue

            if keyword not in line:
                continue

            if self._time_pattern not in line:
                continue

            if not self.IsValid(line, self.filter_words):
                continue


            if 'custom' == self._log_mode:
                extracted_time = self.parseLineForPerformanceInCustomFormat(line, keyword)
            elif 'json' == self._log_mode:
                extracted_time = self.parseLineForPerformanceInJsonFormat(line, keyword)
            elif 'nginx' == self._log_mode:
                extracted_time = self.parseLineForPerformanceInNginxFormat(line, keyword)
            elif 'csv' == self._log_mode:
                extracted_time = self.parseLineFroPerformanceInCSVFormat(line)

            if extracted_time >= 0:#valid time log line
                self.query_time_array.append(extracted_time)
                if first_query == "":
                    first_query = line
                last_query = line
            if extracted_time >= self.overtime_threshold:
                self.overtime_array.append(line)


        curfile.close()
        if first_query == "" or last_query == "":
            return line_index

        print first_query
        print last_query
        file_start_time = self.ExtractDateTimeFromLog(first_query)
        if 0l == self._total_log_start_time:
            self._total_log_start_time = file_start_time

        file_end_time = self.ExtractDateTimeFromLog(last_query)
        self._total_log_end_time = file_end_time

        print file_start_time
        print file_end_time
        self.total_time_range = self.total_time_range + file_end_time - file_start_time
            
        return line_index

    def GrepFromTxtInFolder(self, folderpath, keyword):
        filelist = os.listdir(folderpath)
        print filelist
        for file in filelist:
            if ".log" in file:
                self.GrepFromTxtInFile(folderpath + "//" + file, keyword)


    def GrepFromTxtInFolderByPattern(self, folderpath, pattern, keyword):
        filelist = os.listdir(folderpath)
        matched_file_list = []        
        for file in filelist:
            if ".log" in file and pattern in file:
                matched_file_list.append(folderpath + "//" + file)
        
        self.GrepFromTxtInFiles(matched_file_list, keyword)

    def GrepFromTxtInFiles(self, filelist, keyword):
        print filelist
        for file in filelist:
            if ".log" in file:
                self.GrepFromTxtInFile(file, keyword)

    def StatsByTimeRanges(self):
        stats_part_count = len(self.value_stats_thresholds)
        for index in range(0, stats_part_count):
            self.output_stats.append(0)

        for value in self.query_time_array:
            for index in range(0, stats_part_count):
                if index < stats_part_count -1:
                    if self.value_stats_thresholds[index] <= value and self.value_stats_thresholds[index+1] > value:
                        self.output_stats[index] = self.output_stats[index]+1
                        break
                else:
                    if self.value_stats_thresholds[index] <= value:
                        self.output_stats[index] = self.output_stats[index]+1
                        break
        self.GetTimeStatsRatio()

        return self.output_stats

    def StatSummary(self):
        avg_time = 0.0
        current_count =0l
        for time_cost in self.query_time_array:
            current_count = current_count + 1
            delta = time_cost - avg_time
            avg_time = avg_time + delta/current_count

        std2_avg = 0.0
        current_count =0l
        for time_cost in self.query_time_array:
            current_count = current_count + 1
            delta2 = (time_cost - avg_time)*(time_cost - avg_time)
            std2_avg = std2_avg + ( delta2 - std2_avg)/current_count

        std = math.sqrt(std2_avg)

        self._avg_time_in_ms_per_request = avg_time
        self._std_time_in_ms = std

        return (avg_time, std)

    def PrintSummaryStats(self):
        time_rate = 1
        if 'ms' == self._record_time_unit:
            time_rate = 1000

        
        print "=========================================="
        print "Test summary results:"
        print "=========================================="

        print str(self._total_log_start_time) + "s"
        ltime=time.localtime(self._total_log_start_time)
        timeStr=time.strftime("%Y-%m-%d %H:%M:%S", ltime)
        print "test start time: " + timeStr

        print str(self._total_log_end_time) + "s"
        ltime=time.localtime(self._total_log_end_time)
        timeStr=time.strftime("%Y-%m-%d %H:%M:%S", ltime)
        print "test end time: " + timeStr

        print "average time cost per request(ms): " + str(self._avg_time_in_ms_per_request)
        print "std.dev time cost(ms): " + str(self._std_time_in_ms)
        print "total requests: " + str(self.GetRequestCount())
        print "qps: " + str(self.GetRequestCount()*1.0/(self.GetTotalTimeForAllRequests()))
        print "=========================================="

    def PrintFixedRatiosStats(self):
        print "=========================================="
        print "Test time distribution by percentages"
        print "=========================================="
        for index in range(0, len(self._ratio_stats)):
            time_cost = self._ratio_stats[index]
            time_ratio = self.stats_ratios[index]

            print "<= " + str(time_ratio*100) + "%: " + str(time_cost) + " ms"

        print "===========================================" 

    def PrintTimeRangeStats(self):
        print "==========================================="
        print "Test time distribution by fixed time ranges"
        print "==========================================="
        print '用于统计的时间区间和区间内请求数量分别为：'
        print self.value_stats_thresholds
        print self.output_stats
        print self.output_stats_ratio
        print '最终请求响应时间分布结果为：'
        for index in range(0, len(self.value_stats_thresholds)):
            if index < (len(self.value_stats_thresholds) -1):
                print "[" + str(self.value_stats_thresholds[index]) + "," + str(self.value_stats_thresholds[index+1]) +"): " + str(self.output_stats[index]) + ', ' + str(self.output_stats_ratio[index]*100) + "%"
            else:
                print "[" + str(self.value_stats_thresholds[index]) + ", ~ ): "+ str(self.output_stats[index]) + ', ' + str(self.output_stats_ratio[index]*100) + "%"
        print "============================================"       


    def StatsByFixedRatios(self):
        
        self.query_time_array.sort()
        total_query_count = len(self.query_time_array)
        self._ratio_stats = []
        for ratio in self.stats_ratios:
            index = int(total_query_count*ratio)    
            if index > total_query_count - 1:
                index =  total_query_count - 1       
            self._ratio_stats.append(self.query_time_array[index])

        return self._ratio_stats

    def Average(self):
        array_size = len(self.query_time_array)
        total_time_cost=0.0
        for i in range(0, array_size):
            total_time_cost = total_time_cost + self.query_time_array[i]

        average_time_cost = total_time_cost/array_size
        return average_time_cost

    def QueryPerSecond(self):
        
        totla_request_count = len(self.query_time_array)
        querry_per_second = round(totla_request_count/self.total_time_range, 1)
        
        return querry_per_second

    def PrintOvertimeLogs(self):
        if "csv" == self._log_mode:
            return
        for line in self.overtime_array:
            print line

    def GetOvertimeCount(self):
        return len(self.overtime_array)