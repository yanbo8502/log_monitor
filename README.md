# log_monitor
log_monitor configuration/cache file instrustion:

[basic]
log_dir = [log dir absolute root path], optional, the exteranl input value with commanline is preferred.

log_name_prefix = [logprefix, the prefiex of the log file name, to filter the files which are not out targets]

log_type = [json, csv, regx or custom] this format is used to parse the query information lines, which contain some key--value recordsing the performance or clienct parametres of each request, in log file, of no parsing needed, only key-string matching and counting, this setting will be ignored.

enable = [true, fasle] if set false, the whole program will do nothing  even if started

emails = [a@xxxx.com,b@xxxx.com] mail addresses to send alert mail to, comma delimated

phones = [138xxxxxxx9,138xxxxxxx6] phone number to send alert message to, comma delimated

last_file = [/service_dir/log/xxxxxxxx_20161002.log, eg. Absolute file path at which the program stop at during last time of process]

lines = [line number of the file  at which the program stop at during last time of process, 100, eg]

[error_words_monitor]
email_subject = [日志异常信息过多报警, eg] A brief title trunck-content to inform receiver the severity category, the program will add some other information to it, for example, the monitorer server host.

email_content = [指定时间内异常信息过多，请处理, eg] A brief content specially for this monitor, to explain this alert, the detail information, for example, how musch eceptions occured, will be added by program.

settings = [ A json value, like {"keyword1": {"count": 0, "stats_interval": 30, "start_time": 1475146174, "count_threshold": 50}, "keyword2": {"count": 0, "stats_interval": 20, "start_time": 1475146174, "count_threshold": 20}}] the monitor can monitor  multiple error keywords in log file,diffrent keywords represent different kinds of problem, so each key word should have a different monitor and alert rule, this is why we use json to record diffrent keywords' settings.

monitor_words = [keyword1,keyword2,... , eg] comma-delimited value to match keywords setting

enable = [true, fasle] if set false, thie monitor will not be implemented

[target_words_monitor]
target_words =  [keyword1,keyword2,... , eg] comma-delimited value to set the monitor special words

email_subject = [目标词监控报警, eg] A brief title trunck-content specially for this monitor, to inform receiver the severity category, the program will add some other information to it, for example, the monitorer server host.

email_content = [目标词日志出现 部分日志内容已经截取，如下所示，请进行处理, eg]
enable = [true, fasle] if set false, thismonitor will not be implemented

[user_request_monitor]
target_words = [target log line keyword] to extract the line of the user-request information among other log information lines

log_paras = {'prefix':0,'reqStartTime':1,'reqStartTimeStr':2, 'direct_client_host': 3 , 'direct_client_port':4 , 'real_client_host':5 , 'server_mark' :6 , 'request_uri' : 7, 'uid' : 8, 'devide_id' : 9, 'device_type' : 10 , 'response_time':11}, eg. json-format setting, each key represents one property in "user request reocord line " in the log. the value-number of each key means the position(column) index of the property in comma-splitted format line of user request in CSV log type.

log_paras_type = {'prefix':'string','reqStartTime':'datetime','reqStartTimeStr':'string', 'direct_client_host': 'string' , 'direct_client_port':'int' , 'real_client_host':'string' , 'server_mark' :'string' , 'request_uri' : 'string', 'uid' :'string', 'devide_id' : 'string', 'device_type' : 'string' , 'response_time':'int'}, eg. json-format setting, each key represents one property in "user request reocord line " in the log. the data-format-value of each key means the value-format of the property in comma-splitted format line of user request in CSV log type.  This can help parsing the properties. 

log_regx = regx formtat strings. This is used to parsre and extract values written in some  log-line which has more compliated format than json or CSV, such as  the nginx default log format. Of course, we recommend the log is writtetn with simple format.  

timestamp_unit = s

enable = [true, fasle] if set false, this monitor will not be implemented

[overtime_monitor]

log_regx = regx formtat strings. This is used to parsre and extract values written in some  log-line which has more compliated format than json or CSV, such as  the nginx default log format. Of course, we recommend the log is writtetn with simple format.  

request_time_unit = [s or ms, use to decide how to convert the digit of timestamp to seconds]

request_time_index = [2, eg. the position index of the timestamp information of user request in CSV-format log line]

request_time_key = [reqStartTimeStr, eg, key-name of request timestamp in json-format 
log line]

time_format = [date-time format like '%Y-%m-%d %H:%M:%S', or 'number', eg] 
date-time-format, widely used by timestamp-string convertion in many languages like C++, java, python. This is used to convert the string format like '2016-10-12 14:21:16' to number 1476253276 with unit of 'seconds'. if this setting value is set to 'number', the timestamp in log line is already time number like 1476253276 and no convertion is needed.

time_cost_index =  [11, eg. the position index of the properyt of response-time (the time-cost which server takes to process the user request and get the return value) in CSV-format log line]

time_cost_key = [response_time, eg], used for json log-type,to indentify which key in json mean the time-cost property

time_cost_unit = [s or ms, use to decide how to convert the number of time-cost to milliseconds]

monitor_word = [keyword to extract the line of the user-request information among other log information lines]

count_threshold = [1000, eg] If the over-time user requests exceeds this number limit within a time-window, altert will be triggered

time_threshold = [300, eg, in unit of seconds] if the time-cost to process  one user-request exceed the time limit, the over-time count will increased by one.

start_time = [1475213564, eg] The start time-stamp number of one time-window

stats_interval = [300, eg, in unit of seconds] stats_inrterval is the time window of the monitor to do the statistics, within one time-window, the monitor may process and count the log files increasingly more than one time.

count = [0, eg] The current accumulated over-time counts in the time-window.

email_subject = 超时过多报警

email_content = 在指定时间内，超时请求过多，服务器的性能存在异常，请处理（考虑切换备份）。

enable = [true, fasle] if set false, thismonitor will not be implemented


#log_stats_for_time
time_format = [date-time format like '%Y-%m-%d %H:%M:%S', or 'number', eg] date-time-format, widely used by timestamp-string convertion in many languages like C++, java, python. This is used to convert the string format like '2016-10-12 14:21:16' to number 1476253276 with unit of 'seconds'. if this setting value is set to 'number', the timestamp in log line is already time number like 1476253276 and no convertion is needed.

keyword = [keyword to extract the line of the user-request information among other log information lines]

request_time_index = [2, eg. the position index of the timestamp information of user request in CSV-format log line]

time_cost_index =  [11, eg. the position index of the property of response-time (the time-cost which server takes to process the user request and get the return value) in CSV-format log line]

record_time_unit = [s or ms, use to decide how to convert the digit of timestamp to seconds]

time_cost_unit = [s or ms, use to decide how to convert the number of time-cost to milliseconds]

log_regx = regx formtat strings. This is used to parsre and extract values written in some  log-line which has more compliated format than json or CSV, such as  the nginx default log format. Of course, we recommend the log is writtetn with simple format.  

request_time_key = [reqStartTimeStr, eg, key-name of request timestamp in json-format 
log line]

time_cost_key = [response_time, eg], used for json log-type,to indentify which key in json mean the time-cost property

