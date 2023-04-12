# -*- codeing = utf-8 -*-
# @Time : 2023-02-16 3:37 p.m.
# @Author: weijiazhao
# @File : logRecorder.py
# @Software: PyCharm

import datetime
import csv
import os
import configuration


def record_to_log(action: str, log):
    timezone = configuration.get_timezone()
    local_Time = datetime.datetime.utcnow() + datetime.timedelta(hours=int(timezone))

    folder = os.path.expanduser(str(configuration.get_logdir()+'Log'))
    if not os.path.exists(folder):  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(folder)  # makedirs 创建文件时如果路径不存在会创建这个路径

    with open((folder + "/log-%s.txt" % local_Time.strftime("%Y%m%d")), 'a', encoding='gb18030', errors='ignore') as file:
        file.write(">>" + str(local_Time)+f"(Timezone: {timezone})----------------------------------------------\n")
        file.write(">>Action:" + action + '\n')
        file.write(str(log) + '\n')
        file.close()

# 写入文件
def save_to_csv(dataString, API):
    # 根据UTC时间，换算成中国区域时间
    timezone = int(configuration.get_timezone())
    folder = os.path.expanduser(str(configuration.get_logdir()+'Log'))
    if not os.path.exists(folder):  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(folder)  # makedirs 创建文件时如果路径不存在会创建这个路径

    nowDateTime = datetime.datetime.utcnow() + datetime.timedelta(hours=timezone)
    nowDate = nowDateTime.strftime("%Y%m%d")

    filename = f'{folder}/{API}_{nowDate}.csv'
    # print("folder:", folder)
    # print("filename:", filename)
    if not os.path.exists(filename):  # 判断文件是否存在,如果不存在则创建新文件
        with open(filename, mode='w', newline='', encoding='gb18030', errors='ignore') as cf:
            wf = csv.writer(cf)
            title = ['StatusCode', 'Status', 'Time', 'Name', 'Type', 'URL', 'Interval', 'Content', 'Remarks[scNr, feedPhase, unsupportedPhase]']
            wf.writerow(title)
            wf.writerow(dataString)
            wf.close()
    else:
        # 末尾追加写入，文件必须已存在
        with open(filename, mode='a', newline='', encoding='gb18030', errors='ignore') as cfa:
            wf = csv.writer(cfa)
            wf.writerow(dataString)
            wf.close()
