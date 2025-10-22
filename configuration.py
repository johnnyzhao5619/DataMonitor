# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 4:14 p.m.
# @Author: weijiazhao
# @File : configuration.py
# @Software: PyCharm
import configparser


def get_logdir():
    logdir = "./APIMonitor/"
    config = configparser.RawConfigParser()
    config.read(logdir)
    return logdir

def read_monitor_list():
    logdir = get_logdir()
    monitorlist = []
    config = configparser.RawConfigParser()
    config.read(logdir+"Config/Config.ini")
    totalNumber = config.get('MonitorNum', 'total')
    for i in range(int(totalNumber)):
        monitordir = {}
        monitordir['name'] = config.get(f'Monitor{i+1}', 'name')
        monitordir['url'] = config.get(f'Monitor{i+1}', 'url')
        monitordir['type'] = config.get(f'Monitor{i+1}', 'type')
        monitordir['interval'] = config.get(f'Monitor{i+1}', 'interval')
        monitordir['email'] = config.get(f'Monitor{i+1}', 'email')
        monitorlist.append(monitordir)
        del monitordir

    return monitorlist

def read_mail_configuration():
    logdir = get_logdir()
    mailconfig={}
    config = configparser.RawConfigParser()
    config.read(logdir+"Config/Config.ini")
    mailconfig['smtp_server'] = config.get('Mail', 'smtp_server')
    mailconfig['smtp_port'] = config.get('Mail', 'smtp_port')
    mailconfig['username'] = config.get('Mail', 'username')
    mailconfig['password'] = config.get('Mail', 'password')
    mailconfig['from_addr'] = config.get('Mail', 'from_addr')
    mailconfig['to_addrs'] = config.get('Mail', 'to_addrs')
    print("mailconfig:", mailconfig)
    return mailconfig

def get_timezone():
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+"Config/Config.ini")
    return config.get('TimeZone', 'timezone')

def set_timezone(timezone):
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+"Config/Config.ini")
    if not config.has_section('TimeZone'):
        config.add_section('TimeZone')
    config.set('TimeZone', 'timezone', timezone)
    with open(logdir + "Config/Config.ini", "w") as configfile:
        config.write(configfile)




def writeconfig(configDir: str):
    info = configparser.ConfigParser()
    info.add_section("General")
    info.set("General", "app_name", "Monitor Everything")
    info.set("General", "version", "0.2")

    info.add_section("Logging")
    info.set("Logging", "log_level", "info")
    info.set("Logging", "log_file", "~/Downloads/APIMonitor/")

    info.add_section("TimeZone")
    info.set("TimeZone", "timezone", "8")

    info.add_section("Mail")
    info.set("Mail", "smtp_server", "smtp-mail.outlook.com")
    info.set("Mail", "smtp_port", "587")
    info.set("Mail", "username", "OperationTeam_tds@outlook.com")
    info.set("Mail", "password", "1qaz2wsx#EDC")
    info.set("Mail", "from_addr", "OperationTeam_tds@outlook.com")
    info.set("Mail", "to_addrs", "johnnyzhao5619@gmail.com")
    info.set("Mail", "subject", "Outage Warning！")

    info.add_section("MonitorNum")
    info.set("MonitorNum", "total", "5")

    info.add_section("Monitor1")
    info.set("Monitor1", "name", "Baidu-For Test")
    info.set("Monitor1", "url", "http://www.baidu.com")
    info.set("Monitor1", "type", "SERVER")
    info.set("Monitor1", "interval", "60")
    info.set("Monitor1", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor2")
    info.set("Monitor2", "name", "Wuxi Data Provider")
    info.set("Monitor2", "url", "36.155.95.59:28080/JKS_Server/SysInfo")
    info.set("Monitor2", "type", "SERVER")
    info.set("Monitor2", "interval", "1800")
    info.set("Monitor2", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor3")
    info.set("Monitor3", "name", "Nanjing Data Provider")
    info.set("Monitor3", "url", "101.132.145.141:42887")
    info.set("Monitor3", "type", "SERVER")
    info.set("Monitor3", "interval", "1800")
    info.set("Monitor3", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor4")
    info.set("Monitor4", "name", "Wuhan Data Provider")
    info.set("Monitor4", "url", "c2v.huali-cloud.com/auth/servicesList")
    info.set("Monitor4", "type", "SERVER")
    info.set("Monitor4", "interval", "1800")
    info.set("Monitor4", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor5")
    info.set("Monitor5", "name", "CN01-CN02")
    info.set("Monitor5", "url", "219.239.83.74")
    info.set("Monitor5", "type", "SERVER")
    info.set("Monitor5", "interval", "1800")
    info.set("Monitor5", "email", "johnnyzhao56192@gmail.com")

    info.write(open(('./APIMonitor/Config/Config.ini'), "w"))