#一些参赛在command line以及配置文件.ini里都可以进行配置，command line参数的优先级高。
#日志增量扫描报警
cd $log_monitor/code
python log_monitor.py  -c ../sample/overtime_monitor_csv_sample.ini -r ../sample/sample_logs/log_csv
#不打印有价值的信息，结果是缓存和可能的报警

#日志分析统计，结果打印出来。
cd $log_monitor/code
python log_stats_for_time.py -t csv --log_conf=log_stat_for_time_csv_sample.ini -f testlogs/log_csv/
#result sample
:`
==========================================
Test summary results:
==========================================
1485093015s
test start time: 2017-01-22 21:50:15
1485100799s
test end time: 2017-01-22 23:59:59
average time cost per request(ms): 0.358193707621
std.dev time cost(ms): 3.53387028572
total requests: 588299
qps: 75.6
==========================================
==========================================
Test time distribution by percentages
==========================================
<= 50.0%: 0 ms
<= 90.0%: 0 ms
<= 95.0%: 1 ms
<= 99.0%: 1 ms
<= 99.9%: 49 ms
<= 99.99%: 83 ms
<= 100.0%: 132 ms
===========================================
===========================================
Test time distribution by fixed time ranges
===========================================
用于统计的时间区间和区间内请求数量分别为：
[0, 50, 100, 300, 500, 1000, 3000]
[587785, 504, 10, 0, 0, 0, 0]
[0.9991, 0.0009, 0.0, 0.0, 0.0, 0.0, 0.0]
最终请求响应时间分布结果为：
[0,50): 587785, 99.91%
[50,100): 504, 0.09%
[100,300): 10, 0.0%
[300,500): 0, 0.0%
[500,1000): 0, 0.0%
[1000,3000): 0, 0.0%
[3000, ~ ): 0, 0.0%
============================================
log-analyzing time cost:
8.06580591202 ms

`

