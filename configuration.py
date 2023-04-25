# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 4:14 p.m.
# @Author: weijiazhao
# @File : configuration.py
# @Software: PyCharm
import configparser


def get_logdir():
    logdir = './APIMonitor/'
    config = configparser.RawConfigParser()
    config.read(logdir + 'Config/Config.ini')
    return logdir

def get_mail_format():
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/Config.ini')


def read_general():
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/Config.ini')
    appname = config.get('General', 'app_name')
    version = config.get('General', 'version')
    return appname, version

def read_log_settings():
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir + 'Config/Config.ini')
    auto_update = config.get('Logging', 'auto_update_signal_num')
    return auto_update

def read_monitor_list():
    logdir = get_logdir()
    monitorlist = []
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/MonitorList.ini')
    totalNumber = config.get('MonitorNum', 'total')
    for i in range(int(totalNumber)):
        monitordir = {}
        monitordir['name'] = config.get(f'Monitor{i+1}', 'name')
        monitordir['url'] = config.get(f'Monitor{i+1}', 'url')
        monitordir['type'] = config.get(f'Monitor{i+1}', 'type')
        monitordir['format'] = config.get(f'Monitor{i+1}', 'format')
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
    config.read(logdir+'Config/Config.ini')
    return config.get('TimeZone', 'timezone')

def get_server_ip():
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/Config.ini')
    server_list = config.items('Server_IP')
    return server_list

def get_targetnum(target:str):
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/Config.ini')
    targetNumber = config.get('Region_Expected_Targets', target)
    return targetNumber

def set_targetnum(target:str, num:str):
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/Config.ini')
    config.set('Region_Expected_Targets', target, num)
    with open((logdir + "Config/Config.ini"), "w") as f:
        config.write(f)

def set_timezone(timezone):
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/Config.ini')
    config.set('TimeZone', 'timezone', timezone)
    with open((logdir + "Config/Config.ini"), "w") as f:
        config.write(f)

def get_mail_formate(mail_type:str):
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir+'Config/Config.ini')
    mail_content = config.get('MailContent', mail_type)
    return mail_content


def write_mailSample(mailSampleDir:str):
    outage_mail = configparser.ConfigParser()
    outage_mail.add_section("OutageNotificationMailSample")
    outage_mail.set("OutageNotificationMailSample", "Subject", "abcd")
    outage_mail.set("OutageNotificationMailSample", "body", "abcd")
    outage_mail.write(open((mailSampleDir+'/OutageNotificationMailSample.html'), "w"))

    outage_resolution_mail = configparser.ConfigParser()
    outage_resolution_mail.add_section("OutageNotificationResolutionMailSample")
    outage_resolution_mail.set("OutageNotificationResolutionMailSample", "Subject", "abcd")
    outage_resolution_mail.set("OutageNotificationResolutionMailSample", "body", "abcd")
    outage_resolution_mail.write(open((mailSampleDir+'/OutageNotificationResolutionMailSample.html'), "w"))


    incomplete_mail = configparser.ConfigParser()
    incomplete_mail.add_section("PhaseIncompleteNotificationMailSample")
    incomplete_mail.set("PhaseIncompleteNotificationMailSample", "Subject", "abcd")
    incomplete_mail.set("PhaseIncompleteNotificationMailSample", "body", "abcd")
    incomplete_mail.write(open((mailSampleDir+'/PhaseIncompleteNotificationMailSample.html'), "w"))


    incomplete_resolution_mail = configparser.ConfigParser()
    incomplete_resolution_mail.add_section("PhaseIncompleteNotificationResolutionMailSample")
    incomplete_resolution_mail.set("PhaseIncompleteNotificationResolutionMailSample", "Subject", "abcd")
    incomplete_resolution_mail.set("PhaseIncompleteNotificationResolutionMailSample", "body", "abcd")
    incomplete_resolution_mail.write(open((mailSampleDir+'/PhaseIncompleteNotificationResolutionMailSample.html'), "w"))

def write_config(configDir: str):
    info = configparser.ConfigParser()
    info.add_section("General")
    info.set("General", "app_name", "Monitor Everything")
    info.set("General", "version", "0.9")

    info.add_section("Logging")
    info.set("Logging", "log_level", "info")
    info.set("Logging", "log_file", "./APIMonitor/")
    info.set("Logging", "auto_update_signal_num", "0")

    info.add_section("TimeZone")
    info.set("TimeZone", "timezone", "8")

    info.add_section("TimeZone")
    info.set("TimeZone", "timezone", "8")

    info.add_section("Server_IP")
    info.set("Server_IP", "Beijing", "49.233.41.147")
    info.set("Server_IP", "Nanjing-Live", "49.232.78.244")
    info.set("Server_IP", "Nanjing-Lab", "101.42.254.16")
    info.set("Server_IP", "Wuhan", "49.233.41.147")
    info.set("Server_IP", "Wuxi", "101.42.254.16")
    info.set("Server_IP", "Xian", "101.42.159.132")

    info.add_section("Region_Expected_Targets")
    info.set("Region_Expected_Targets", "Beijing", "22")
    info.set("Region_Expected_Targets", "Nanjing-Live", "157")
    info.set("Region_Expected_Targets", "Nanjing-Lab", "427")
    info.set("Region_Expected_Targets", "Wuhan", "250")
    info.set("Region_Expected_Targets", "Wuxi", "1139")
    info.set("Region_Expected_Targets", "Xian", "0")

    info.add_section("Mail")
    info.set("Mail", "smtp_server", "smtp-mail.outlook.com")
    info.set("Mail", "smtp_port", "587")
    info.set("Mail", "username", "OperationTeam_tds@outlook.com")
    info.set("Mail", "password", "1qaz2wsx#EDC")
    info.set("Mail", "from_addr", "OperationTeam_tds@outlook.com")
    info.set("Mail", "to_addrs", "johnnyzhao5619@gmail.com")
    info.set("Mail", "subject", "Outage Warning")

    # info.add_section("MonitorNum")
    # info.set("MonitorNum", "total", "15")
    #
    # info.add_section("Monitor1")
    # info.set("Monitor1", "name", "For Test")
    # info.set("Monitor1", "url", "http://www.baidu.com")
    # info.set("Monitor1", "type", "SERVER")
    # info.set("Monitor1", "format", "HTTP")
    # info.set("Monitor1", "interval", "60")
    # info.set("Monitor1", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor2")
    # info.set("Monitor2", "name", "Wuxi Phase Continuity")
    # info.set("Monitor2", "url", "101.42.254.16:6741/PSA/Services/GetPhaseContinuity?region=China.Wuxi&format=xml")
    # info.set("Monitor2", "type", "GET")
    # info.set("Monitor2", "format", "XML")
    # info.set("Monitor2", "interval", "900")
    # info.set("Monitor2", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor3")
    # info.set("Monitor3", "name", "Nanjing-live Phase Continuity")
    # info.set("Monitor3", "url", "49.232.78.244:6741/PSA/Services/GetPhaseContinuity?region=China.Nanjing&format=xml")
    # info.set("Monitor3", "type", "GET")
    # info.set("Monitor3", "format", "XML")
    # info.set("Monitor3", "interval", "900")
    # info.set("Monitor3", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor4")
    # info.set("Monitor4", "name", "Nanjing-lab Phase Continuity")
    # info.set("Monitor4", "url", "101.42.254.16:6741/PSA/Services/GetPhaseContinuity?region=China.Nanjing&format=xml")
    # info.set("Monitor4", "type", "GET")
    # info.set("Monitor4", "format", "XML")
    # info.set("Monitor4", "interval", "900")
    # info.set("Monitor4", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor5")
    # info.set("Monitor5", "name", "Wuhan Phase Continuity")
    # info.set("Monitor5", "url", "49.233.41.147:6741/PSA/Services/GetPhaseContinuity?region=China.Wuhan&format=xml")
    # info.set("Monitor5", "type", "GET")
    # info.set("Monitor5", "format", "XML")
    # info.set("Monitor5", "interval", "900")
    # info.set("Monitor5", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor6")
    # info.set("Monitor6", "name", "Beijing Phase Continuity")
    # info.set("Monitor6", "url", "49.233.41.147:6741/PSA/Services/GetPhaseContinuity?region=China.Beijing&format=xml")
    # info.set("Monitor6", "type", "GET")
    # info.set("Monitor6", "format", "XML")
    # info.set("Monitor6", "interval", "900")
    # info.set("Monitor6", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor7")
    # info.set("Monitor7", "name", "Nanjing Data Provider")
    # info.set("Monitor7", "url", "101.132.145.141:42887")
    # info.set("Monitor7", "type", "SERVER")
    # info.set("Monitor7", "format", "HTTP")
    # info.set("Monitor7", "interval", "900")
    # info.set("Monitor7", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor8")
    # info.set("Monitor8", "name", "Wuhan Data Provider")
    # info.set("Monitor8", "url", "c2v.huali-cloud.com/auth/servicesList")
    # info.set("Monitor8", "type", "SERVER")
    # info.set("Monitor8", "format", "HTTP")
    # info.set("Monitor8", "interval", "900")
    # info.set("Monitor8", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor9")
    # info.set("Monitor9", "name", "Wuxi Data Provider")
    # info.set("Monitor9", "url", "36.155.95.59:28080/JKS_Server/SysInfo")
    # info.set("Monitor9", "type", "GET")
    # info.set("Monitor9", "format", "JSON")
    # info.set("Monitor9", "interval", "900")
    # info.set("Monitor9", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor10")
    # info.set("Monitor10", "name", "CN01-CN02")
    # info.set("Monitor10", "url", "219.239.83.74")
    # info.set("Monitor10", "type", "SERVER")
    # info.set("Monitor10", "format", "HTTP")
    # info.set("Monitor10", "interval", "900")
    # info.set("Monitor10", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor11")
    # info.set("Monitor11", "name", "Wuxi Live Target")
    # info.set("Monitor11", "url", "101.42.254.16:6265/PSA/Services/GetLiveTargets?region=China.Wuxi&format=XML&filter=All")
    # info.set("Monitor11", "type", "GET")
    # info.set("Monitor11", "format", "XML")
    # info.set("Monitor11", "interval", "900")
    # info.set("Monitor11", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor12")
    # info.set("Monitor12", "name", "Nanjing-live Live Target")
    # info.set("Monitor12", "url", "49.232.78.244:6265/PSA/Services/GetLiveTargets?region=China.Nanjing&format=XML&filter=All")
    # info.set("Monitor12", "type", "GET")
    # info.set("Monitor12", "format", "XML")
    # info.set("Monitor12", "interval", "900")
    # info.set("Monitor12", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor13")
    # info.set("Monitor13", "name", "Nanjing-lab Live Target")
    # info.set("Monitor13", "url", "101.42.254.16:6265/PSA/Services/GetLiveTargets?region=China.Nanjing&format=XML&filter=All")
    # info.set("Monitor13", "type", "GET")
    # info.set("Monitor13", "format", "XML")
    # info.set("Monitor13", "interval", "900")
    # info.set("Monitor13", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor14")
    # info.set("Monitor14", "name", "Wuhan Live Target")
    # info.set("Monitor14", "url", "49.233.41.147:6265/PSA/Services/GetLiveTargets?region=China.Wuhan&format=XML&filter=All")
    # info.set("Monitor14", "type", "GET")
    # info.set("Monitor14", "format", "XML")
    # info.set("Monitor14", "interval", "900")
    # info.set("Monitor14", "email", "johnnyzhao56192@gmail.com")
    #
    # info.add_section("Monitor15")
    # info.set("Monitor14", "name", "Beijing Live Target")
    # info.set("Monitor14", "url", "49.233.41.147:6265/PSA/Services/GetLiveTargets?region=China.Beijing&format=XML&filter=All")
    # info.set("Monitor14", "type", "GET")
    # info.set("Monitor14", "format", "XML")
    # info.set("Monitor14", "interval", "900")
    # info.set("Monitor14", "email", "johnnyzhao56192@gmail.com")


    info.write(open((configDir+"/Config.ini"), "w"))


def write_monitor_list(configDir: str):
    info = configparser.ConfigParser()
    info.add_section("MonitorNum")
    info.set("MonitorNum", "total", "15")

    info.add_section("Monitor1")
    info.set("Monitor1", "name", "For Test")
    info.set("Monitor1", "url", "http://www.baidu.com")
    info.set("Monitor1", "type", "SERVER")
    info.set("Monitor1", "format", "HTTP")
    info.set("Monitor1", "interval", "60")
    info.set("Monitor1", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor2")
    info.set("Monitor2", "name", "Wuxi Phase Continuity")
    info.set("Monitor2", "url", "101.42.254.16:6741/PSA/Services/GetPhaseContinuity?region=China.Wuxi&format=xml")
    info.set("Monitor2", "type", "GET")
    info.set("Monitor2", "format", "XML")
    info.set("Monitor2", "interval", "900")
    info.set("Monitor2", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor3")
    info.set("Monitor3", "name", "Nanjing-live Phase Continuity")
    info.set("Monitor3", "url", "49.232.78.244:6741/PSA/Services/GetPhaseContinuity?region=China.Nanjing&format=xml")
    info.set("Monitor3", "type", "GET")
    info.set("Monitor3", "format", "XML")
    info.set("Monitor3", "interval", "900")
    info.set("Monitor3", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor4")
    info.set("Monitor4", "name", "Nanjing-lab Phase Continuity")
    info.set("Monitor4", "url", "101.42.254.16:6741/PSA/Services/GetPhaseContinuity?region=China.Nanjing&format=xml")
    info.set("Monitor4", "type", "GET")
    info.set("Monitor4", "format", "XML")
    info.set("Monitor4", "interval", "900")
    info.set("Monitor4", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor5")
    info.set("Monitor5", "name", "Wuhan Phase Continuity")
    info.set("Monitor5", "url", "49.233.41.147:6741/PSA/Services/GetPhaseContinuity?region=China.Wuhan&format=xml")
    info.set("Monitor5", "type", "GET")
    info.set("Monitor5", "format", "XML")
    info.set("Monitor5", "interval", "900")
    info.set("Monitor5", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor6")
    info.set("Monitor6", "name", "Beijing Phase Continuity")
    info.set("Monitor6", "url", "49.233.41.147:6741/PSA/Services/GetPhaseContinuity?region=China.Beijing&format=xml")
    info.set("Monitor6", "type", "GET")
    info.set("Monitor6", "format", "XML")
    info.set("Monitor6", "interval", "900")
    info.set("Monitor6", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor7")
    info.set("Monitor7", "name", "Nanjing Data Provider")
    info.set("Monitor7", "url", "101.132.145.141:42887")
    info.set("Monitor7", "type", "SERVER")
    info.set("Monitor7", "format", "HTTP")
    info.set("Monitor7", "interval", "900")
    info.set("Monitor7", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor8")
    info.set("Monitor8", "name", "Wuhan Data Provider")
    info.set("Monitor8", "url", "c2v.huali-cloud.com/auth/servicesList")
    info.set("Monitor8", "type", "SERVER")
    info.set("Monitor8", "format", "HTTP")
    info.set("Monitor8", "interval", "900")
    info.set("Monitor8", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor9")
    info.set("Monitor9", "name", "Wuxi Data Provider")
    info.set("Monitor9", "url", "36.155.95.59:28080/JKS_Server/SysInfo")
    info.set("Monitor9", "type", "GET")
    info.set("Monitor9", "format", "JSON")
    info.set("Monitor9", "interval", "900")
    info.set("Monitor9", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor10")
    info.set("Monitor10", "name", "CN01-CN02")
    info.set("Monitor10", "url", "219.239.83.74")
    info.set("Monitor10", "type", "SERVER")
    info.set("Monitor10", "format", "HTTP")
    info.set("Monitor10", "interval", "900")
    info.set("Monitor10", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor11")
    info.set("Monitor11", "name", "Wuxi Live Target")
    info.set("Monitor11", "url", "101.42.254.16:6265/PSA/Services/GetLiveTargets?region=China.Wuxi&format=XML&filter=All")
    info.set("Monitor11", "type", "GET")
    info.set("Monitor11", "format", "XML")
    info.set("Monitor11", "interval", "900")
    info.set("Monitor11", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor12")
    info.set("Monitor12", "name", "Nanjing-live Live Target")
    info.set("Monitor12", "url", "49.232.78.244:6265/PSA/Services/GetLiveTargets?region=China.Nanjing&format=XML&filter=All")
    info.set("Monitor12", "type", "GET")
    info.set("Monitor12", "format", "XML")
    info.set("Monitor12", "interval", "900")
    info.set("Monitor12", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor13")
    info.set("Monitor13", "name", "Nanjing-lab Live Target")
    info.set("Monitor13", "url", "101.42.254.16:6265/PSA/Services/GetLiveTargets?region=China.Nanjing&format=XML&filter=All")
    info.set("Monitor13", "type", "GET")
    info.set("Monitor13", "format", "XML")
    info.set("Monitor13", "interval", "900")
    info.set("Monitor13", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor14")
    info.set("Monitor14", "name", "Wuhan Live Target")
    info.set("Monitor14", "url", "49.233.41.147:6265/PSA/Services/GetLiveTargets?region=China.Wuhan&format=XML&filter=All")
    info.set("Monitor14", "type", "GET")
    info.set("Monitor14", "format", "XML")
    info.set("Monitor14", "interval", "900")
    info.set("Monitor14", "email", "johnnyzhao56192@gmail.com")

    info.add_section("Monitor15")
    info.set("Monitor15", "name", "Beijing Live Target")
    info.set("Monitor15", "url", "49.233.41.147:6265/PSA/Services/GetLiveTargets?region=China.Beijing&format=XML&filter=All")
    info.set("Monitor15", "type", "GET")
    info.set("Monitor15", "format", "XML")
    info.set("Monitor15", "interval", "900")
    info.set("Monitor15", "email", "johnnyzhao56192@gmail.com")
    info.write(open((configDir+"/MonitorList.ini"), "w"))