# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 4:14 p.m.
# @Author: weijiazhao
# @File : configuration.py
# @Software: PyCharm

import configparser

def read_monitor_list():
    monitorlist = []
    config = configparser.RawConfigParser()
    config.read('config.ini')
    totalNumber = config.get('MonitorNum', 'total')
    for i in range(int(totalNumber)):
        monitordir = {}

        monitordir['name'] = config.get(f'Monitor{i+1}', 'name')
        monitordir['url'] = config.get(f'Monitor{i+1}', 'url')
        monitordir['type'] = config.get(f'Monitor{i+1}', 'type')
        monitordir['interval'] = config.get(f'Monitor{i+1}', 'interval')
        monitordir['threshold'] = config.get(f'Monitor{i+1}', 'threshold')
        monitordir['email'] = config.get(f'Monitor{i+1}', 'email')
        monitorlist.append(monitordir)
        del monitordir

    return monitorlist

def read_mail_configuration():
    mailconfig={}
    config = configparser.RawConfigParser()
    config.read('config.ini')
    mailconfig['smtp_server'] = config.get('Mail', 'smtp_server')
    mailconfig['smtp_port'] = config.get('Mail', 'smtp_port')
    mailconfig['username'] = config.get('Mail', 'username')
    mailconfig['password'] = config.get('Mail', 'password')
    mailconfig['from_addr'] = config.get('Mail', 'from_addr')
    mailconfig['to_addrs'] = config.get('Mail', 'to_addrs')
    print("mailconfig:", mailconfig)
    return mailconfig