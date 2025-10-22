# -*- codeing = utf-8 -*-
# @Time : 2023-02-16 3:37 p.m.
# @Author: weijiazhao
# @File : logRecorder.py
# @Software: PyCharm
import datetime
import csv
from pathlib import Path

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

    folder = Path(configuration.get_logdir()) / "Log"
    folder.mkdir(parents=True, exist_ok=True)

    log_path = folder / f"log-{chinaDateTime.strftime('%Y%m%d')}.txt"
    with log_path.open("a") as file:
        file.write(">>" + str(chinaDateTime)+"(China Time)----------------------------------------------\n")
        file.write(">>Action:" + action + '\n')
        file.write(str(log) + '\n')
        file.close()
    # 写入文件


def saveToFile(dataString, API):
    # 根据UTC时间，换算成中国区域时间

    folder = Path(configuration.get_logdir()) / "Log"
    folder.mkdir(parents=True, exist_ok=True)

    nowDateTime = _now_with_timezone()
    nowDate = nowDateTime.strftime("%Y%m%d")

    filename = folder / f"{API}_{nowDate}.csv"
    if not filename.exists():  # 判断文件是否存在,如果不存在则创建新文件
        with filename.open(mode='w', newline='', encoding='utf8') as cf:
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
        with filename.open(mode='a', newline='', encoding='utf8') as cfa:
            wf = csv.writer(cfa)
            wf.writerow(dataString)

# b = ['aaa','vvvv','ssss','wwww','gggg','qqqq','rrrr','yyyy']
# saveToFile(b, 'test')