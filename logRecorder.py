# -*- codeing = utf-8 -*-
# @Time : 2023-02-16 3:37 p.m.
# @Author: weijiazhao
# @File : logRecorder.py
# @Software: PyCharm
import datetime
import csv
import os
import configuration


def _now_with_timezone():
    try:
        timezone = int(configuration.get_timezone())
    except (TypeError, ValueError):
        timezone = 0
    utc_now = datetime.datetime.utcnow()
    return utc_now + datetime.timedelta(hours=timezone)


def record(action: str, log):
    chinaDateTime = _now_with_timezone()

    folder = os.path.expanduser(str(configuration.get_logdir()+'Log'))
    if not os.path.exists(folder):  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(folder)  # makedirs 创建文件时如果路径不存在会创建这个路径

    with open((folder + "/log-%s.txt" % chinaDateTime.strftime("%Y%m%d")), "a") as file:
        file.write(">>" + str(chinaDateTime)+"(China Time)----------------------------------------------\n")
        file.write(">>Action:" + action + '\n')
        file.write(str(log) + '\n')
        file.close()
    # 写入文件


def saveToFile(dataString, API):
    # 根据UTC时间，换算成中国区域时间

    folder = os.path.expanduser(str(configuration.get_logdir()+'Log'))
    if not os.path.exists(folder):  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(folder)  # makedirs 创建文件时如果路径不存在会创建这个路径

    nowDateTime = _now_with_timezone()
    nowDate = nowDateTime.strftime("%Y%m%d")

    filename = f'{folder}/{API}_{nowDate}.csv'
    if not os.path.exists(filename):  # 判断文件是否存在,如果不存在则创建新文件
        with open(filename, mode='w', newline='', encoding='utf8') as cf:
            wf = csv.writer(cf)
            title = ['Time', 'API', 'Type', 'url', 'Interval', 'Code', 'Status']

            print("title:", title)
            print("title:", len(title))
            print("dataString:", dataString)
            print("dataString:", len(dataString))
            wf.writerow(title)
            wf.writerow(dataString)
    else:
        # 末尾追加写入，文件必须已存在
        with open(filename, mode='a', newline='', encoding='utf8') as cfa:
            wf = csv.writer(cfa)
            wf.writerow(dataString)

# b = ['aaa','vvvv','ssss','wwww','gggg','qqqq','rrrr','yyyy']
# saveToFile(b, 'test')