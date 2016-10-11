# log_monitor
log_monitor configuration/cache file instrustion:
[basic]
log_name_prefix = [logprefix, the prefiex of the log file name, to filter the files which are not out targets]
log_type = [json, csv, nginx or custom] this format is used to parse the query information lines, which contain some key--value recordsing the performance or clienct parametres of each request, in log file, of no parsing needed, only key-string matching and counting, this setting will be ignored.
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
enable = [true, fasle] if set false, thie monitor will not be implemented

[user_request_monitor]
target_words = [target log line keyword]
log_paras = {'prefix':0,'reqStartTime':1,'reqStartTimeStr':2, 'direct_client_host': 3 , 'direct_client_port':4 , 'real_client_host':5 , 'server_mark' :6 , 'request_uri' : 7, 'uid' : 8, 'devide_id' : 9, 'device_type' : 10 , 'response_time':11}
log_paras_type = {'prefix':'string','reqStartTime':'datetime','reqStartTimeStr':'string', 'direct_client_host': 'string' , 'direct_client_port':'int' , 'real_client_host':'string' , 'server_mark' :'string' , 'request_uri' : 'string', 'uid' :'string', 'devide_id' : 'string', 'device_type' : 'string' , 'response_time':'int'}
timestamp_unit = s
enable = false

[overtime_monitor]
request_time_unit = [s or ms, use to decide how to convert the digit of timestamp to seconds]
request_time_index = [2, eg. the position index of the different information in CSV-format log line]
request_time_key = [reqStartTimeStr, eg, key-name of request timestamp in json-format log line]
time_format = %Y-%m-%d %H:%M:%S
time_cost_index = 11
time_cost_key = response_time
time_cost_unit = ms
monitor_word = [audience_service::user2audience][JSON]
threshold = 5
time_threshold = 2
start_time = 1475213564
stats_interval = 30
count = 0
email_subject = 超时过多报警
email_content = 在指定时间内，超时请求过多，服务器的性能存在异常，请处理（考虑切换备份）。
enable = true
