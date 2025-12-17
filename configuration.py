# -*- codeing = utf-8 -*-
# @Time : 2024-10-22 4:14 p.m.
# @Author: weijiazhao
# @File : configuration.py

import configparser
import json
import os

log_dir = './API Monitor/'
TEMPLATE_SECTION = 'Templates'


def _config_path(*parts: str) -> str:
    """Build a path under the configured base directory."""
    return os.path.join(log_dir, *parts)


def _read_config(file_name: str) -> configparser.RawConfigParser:
    """Helper to load a config file under Config/."""
    cfg = configparser.RawConfigParser()
    cfg.read(_config_path('Config', file_name))
    return cfg


def get_log_dir():
    global log_dir
    return log_dir


# def read_log_settings():
#     log_dir = get_log_dir()
#     config = configparser.RawConfigParser()
#     config.read(log_dir + 'Config/Config.ini')
#     auto_update = config.get('Logging', 'auto_update_signal_num')
#     return auto_update


def get_mail_format():
    return get_mail_content('')


def get_mail_content(mail_type: str) -> str:
    """
    读取邮件模板；缺失时返回空字符串，避免抛异常。
    """
    config = _read_config('Config.ini')
    if not config.has_section('MailContent'):
        return ''
    if not config.has_option('MailContent', mail_type):
        return ''
    return config.get('MailContent', mail_type)


def read_general():
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    appname = config.get('General', 'app_name')
    version = config.get('General', 'version')
    return appname, version


def read_log_settings():
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    auto_update = config.get('Logging', 'auto_update_signal_num')
    return auto_update


def read_monitor_list():
    # log_dir = get_log_dir()
    config = _read_config('MonitorList.ini')
    monitor_list = []
    total = config.get('MonitorNum', 'total')
    for i in range(int(total)):
        monitor_dir = {
            'name': config.get(f'Monitor{i+1}', 'name'),
            'url': config.get(f'Monitor{i+1}', 'url'),
            'type': config.get(f'Monitor{i+1}', 'type'),
            'format': config.get(f'Monitor{i+1}', 'format'),
            'interval': config.get(f'Monitor{i+1}', 'interval'),
            'email': config.get(f'Monitor{i+1}', 'email'),
            'payload': config.get(f'Monitor{i+1}', 'payload')
            if config.has_option(f'Monitor{i+1}', 'payload') else ''
            ,
            'headers': json.loads(config.get(f'Monitor{i+1}', 'headers'))
            if config.has_option(f'Monitor{i+1}', 'headers') else {}
        }
        monitor_list.append(monitor_dir)
    return monitor_list


def read_mail_configuration():
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    mailconfig = {
        'smtp_server': config.get('Mail', 'smtp_server'),
        'smtp_port': config.get('Mail', 'smtp_port'),
        'username': config.get('Mail', 'username'),
        'password': config.get('Mail', 'password'),
        'from_addr': config.get('Mail', 'from_addr'),
        # 'to_addrs': config.get('Mail', 'to_addrs'),
    }
    return mailconfig


def get_timezone():
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    return config.get('TimeZone', 'timezone')


def get_server_ip():
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    server_list = config.items('Server_IP')
    return server_list


def get_targetnum(target: str):
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    targetNumber = config.get('Region_Expected_Targets', target)
    return targetNumber


def set_targetnum(target: str, num: str):
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    config.set('Region_Expected_Targets', target, num)
    with open(_config_path("Config", "Config.ini"), "w") as f:
        config.write(f)


def set_timezone(timezone: str) -> None:
    """
    Sets the timezone to the specified value in the configuration file.

    Args:
        timezone (str): The timezone to set. This should be a string in the format of "+/-X", where X is the number of hours offset from UTC.
    Returns:
        None
    """
    # log_dir = get_log_dir()
    config = _read_config('Config.ini')
    config.set('TimeZone', 'timezone', str(timezone))
    with open(_config_path("Config", "Config.ini"), "w") as f:
        config.write(f)


def get_mail_formate(mail_type: str):
    """
    兼容旧拼写，返回邮件模板内容。
    """
    return get_mail_content(mail_type)


def get_template(key: str, default: str = "") -> str:
    """
    Read a configurable template string from the Templates section.
    """
    config = _read_config('Config.ini')
    if config.has_option(TEMPLATE_SECTION, key):
        return config.get(TEMPLATE_SECTION, key)
    return default


def write_mailSample(mailSampleDir: str):
    outage_mail = configparser.ConfigParser()
    outage_mail.add_section("OutageNotificationMailSample")
    outage_mail.set("OutageNotificationMailSample", "Subject", "abcd")
    outage_mail.set("OutageNotificationMailSample", "body", "abcd")
    outage_mail.write(
        open((mailSampleDir + '/OutageNotificationMailSample.html'), "w"))

    outage_resolution_mail = configparser.ConfigParser()
    outage_resolution_mail.add_section(
        "OutageNotificationResolutionMailSample")
    outage_resolution_mail.set("OutageNotificationResolutionMailSample",
                               "Subject", "abcd")
    outage_resolution_mail.set("OutageNotificationResolutionMailSample",
                               "body", "abcd")
    outage_resolution_mail.write(
        open((mailSampleDir + '/OutageNotificationResolutionMailSample.html'),
             "w"))

    incomplete_mail = configparser.ConfigParser()
    incomplete_mail.add_section("PhaseIncompleteNotificationMailSample")
    incomplete_mail.set("PhaseIncompleteNotificationMailSample", "Subject",
                        "abcd")
    incomplete_mail.set("PhaseIncompleteNotificationMailSample", "body",
                        "abcd")
    incomplete_mail.write(
        open((mailSampleDir + '/PhaseIncompleteNotificationMailSample.html'),
             "w"))

    incomplete_resolution_mail = configparser.ConfigParser()
    incomplete_resolution_mail.add_section(
        "PhaseIncompleteNotificationResolutionMailSample")
    incomplete_resolution_mail.set(
        "PhaseIncompleteNotificationResolutionMailSample", "Subject", "abcd")
    incomplete_resolution_mail.set(
        "PhaseIncompleteNotificationResolutionMailSample", "body", "abcd")
    incomplete_resolution_mail.write(
        open((mailSampleDir +
              '/PhaseIncompleteNotificationResolutionMailSample.html'), "w"))


def write_config(config_dir: str):
    info = configparser.ConfigParser()
    info.add_section("General")
    info.set("General", "app_name", "API Monitor")
    info.set("General", "version", "1.3")

    info.add_section("Logging")
    info.set("Logging", "log_level", "info")
    info.set("Logging", "log_file", "./API Monitor/")
    info.set("Logging", "auto_update_signal_num", "0")

    info.add_section("TimeZone")
    info.set("TimeZone", "timezone", "-8")

    info.add_section("Server_IP")
    # info.set("Server_IP", "Beijing", "49.233.41.147")
    # info.set("Server_IP", "Nanjing-Live", "49.232.78.244")
    # info.set("Server_IP", "Nanjing-Lab", "101.42.254.16")
    # info.set("Server_IP", "Wuhan", "49.233.41.147")
    # info.set("Server_IP", "Wuxi", "101.42.254.16")
    # info.set("Server_IP", "Xian", "101.42.159.132")

    info.add_section("Region_Expected_Targets")
    # info.set("Region_Expected_Targets", "Beijing", "22")
    # info.set("Region_Expected_Targets", "Nanjing-Live", "157")
    # info.set("Region_Expected_Targets", "Nanjing-Lab", "427")
    # info.set("Region_Expected_Targets", "Wuhan", "250")
    # info.set("Region_Expected_Targets", "Wuxi", "1139")
    # info.set("Region_Expected_Targets", "Xian", "0")

    info.add_section("Mail")
    info.set("Mail", "smtp_server", "smtp-mail.outlook.com")
    info.set("Mail", "smtp_port", "587")
    info.set("Mail", "username", "psa.support@traffictechservices.com")
    info.set("Mail", "password", "")
    info.set("Mail", "from_addr", "psa.support@traffictechservices.com")
    # info.set("Mail", "to_addrs", "john.zhao@miovision.com")
    # info.set("Mail", "subject", "Outage Warning")

    info.add_section("Templates")
    info.set("Templates", "outage_subject",
             "{timestamp}: {service_name} outage detected")
    info.set("Templates", "outage_body",
             "{service_name} is unreachable at {timestamp}. Remark: {remark}")
    info.set("Templates", "restored_subject",
             "{timestamp}: {service_name} restored")
    info.set("Templates", "restored_body",
             "{service_name} recovered at {timestamp}. Remark: {remark}")
    info.set("Templates", "log_line",
             ">>{time} (Timezone: {timezone})\n>>Action:{action}\n{log}\n")

    info.add_section("MailContent")
    info.set("MailContent", "Outage", "")
    info.set("MailContent", "Outage_Resolution", "")
    info.set("MailContent", "Phase_Incomplete", "")
    info.set("MailContent", "Phase_Incomplete_Resolution", "")
    info.write(open(os.path.join(config_dir, "Config.ini"), "w"))


def ensure_defaults() -> None:
    """
    Ensure base folders and default config files exist for first-time run.
    """
    base_dir = os.path.expanduser(log_dir)
    config_dir = os.path.join(base_dir, "Config")
    log_path = os.path.join(base_dir, "Log")
    mail_dir = os.path.join(base_dir, "MailSample")

    os.makedirs(log_path, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(mail_dir, exist_ok=True)

    config_path = os.path.join(config_dir, "Config.ini")
    monitor_path = os.path.join(config_dir, "MonitorList.ini")
    if not os.path.exists(config_path):
        write_config(config_dir)
    if not os.path.exists(monitor_path):
        write_monitor_list(config_dir)
    # seed mail samples when missing primary file
    sample_file = os.path.join(mail_dir, "OutageNotificationMailSample.html")
    if not os.path.exists(sample_file):
        write_mailSample(mail_dir)


def write_monitor_list(config_dir: str):
    info = configparser.ConfigParser()
    info.add_section("MonitorNum")
    info.set("MonitorNum", "total", "3")
    info.add_section("Monitor1")
    info.set("Monitor1", "name", "Sample HTTP Server")
    info.set("Monitor1", "url", "http://example.com")
    info.set("Monitor1", "type", "SERVER")
    info.set("Monitor1", "format", "HTTP")
    info.set("Monitor1", "interval", "60")
    info.set("Monitor1", "email", "user@example.com")

    info.add_section("Monitor2")
    info.set("Monitor2", "name", "Sample JSON API")
    info.set("Monitor2", "url",
             "api.example.com/v1/health?token=YOUR_TOKEN&returnJSON=yes")
    info.set("Monitor2", "type", "GET")
    info.set("Monitor2", "format", "JSON")
    info.set("Monitor2", "interval", "300")
    info.set("Monitor2", "email", "user@example.com")

    info.add_section("Monitor3")
    info.set("Monitor3", "name", "Sample XML API")
    info.set("Monitor3", "url",
             "xml.example.com/status?region=RegionA&format=xml")
    info.set("Monitor3", "type", "GET")
    info.set("Monitor3", "format", "XML")
    info.set("Monitor3", "interval", "300")
    info.set("Monitor3", "email", "user@example.com")

    # info.add_section("Monitor2")
    # info.set("Monitor2", "name", "Wuxi Phase Continuity")
    # info.set(
    #     "Monitor2", "url",
    #     "101.42.254.16:6741/PSA/Services/GetPhaseContinuity?region=China.Wuxi&format=xml"
    # )
    # info.set("Monitor2", "type", "GET")
    # info.set("Monitor2", "format", "XML")
    # info.set("Monitor2", "interval", "900")
    # info.set("Monitor2", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor3")
    # info.set("Monitor3", "name", "Nanjing-live Phase Continuity")
    # info.set(
    #     "Monitor3", "url",
    #     "49.232.78.244:6741/PSA/Services/GetPhaseContinuity?region=China.Nanjing&format=xml"
    # )
    # info.set("Monitor3", "type", "GET")
    # info.set("Monitor3", "format", "XML")
    # info.set("Monitor3", "interval", "900")
    # info.set("Monitor3", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor4")
    # info.set("Monitor4", "name", "Nanjing-lab Phase Continuity")
    # info.set(
    #     "Monitor4", "url",
    #     "101.42.254.16:6741/PSA/Services/GetPhaseContinuity?region=China.Nanjing&format=xml"
    # )
    # info.set("Monitor4", "type", "GET")
    # info.set("Monitor4", "format", "XML")
    # info.set("Monitor4", "interval", "900")
    # info.set("Monitor4", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor5")
    # info.set("Monitor5", "name", "Wuhan Phase Continuity")
    # info.set(
    #     "Monitor5", "url",
    #     "49.233.41.147:6741/PSA/Services/GetPhaseContinuity?region=China.Wuhan&format=xml"
    # )
    # info.set("Monitor5", "type", "GET")
    # info.set("Monitor5", "format", "XML")
    # info.set("Monitor5", "interval", "900")
    # info.set("Monitor5", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor6")
    # info.set("Monitor6", "name", "Beijing Phase Continuity")
    # info.set(
    #     "Monitor6", "url",
    #     "49.233.41.147:6741/PSA/Services/GetPhaseContinuity?region=China.Beijing&format=xml"
    # )
    # info.set("Monitor6", "type", "GET")
    # info.set("Monitor6", "format", "XML")
    # info.set("Monitor6", "interval", "900")
    # info.set("Monitor6", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor7")
    # info.set("Monitor7", "name", "Nanjing Data Provider")
    # info.set("Monitor7", "url", "101.132.145.141:42887")
    # info.set("Monitor7", "type", "SERVER")
    # info.set("Monitor7", "format", "HTTP")
    # info.set("Monitor7", "interval", "900")
    # info.set("Monitor7", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor8")
    # info.set("Monitor8", "name", "Wuhan Data Provider")
    # info.set("Monitor8", "url", "c2v.huali-cloud.com/auth/servicesList")
    # info.set("Monitor8", "type", "SERVER")
    # info.set("Monitor8", "format", "HTTP")
    # info.set("Monitor8", "interval", "900")
    # info.set("Monitor8", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor9")
    # info.set("Monitor9", "name", "Wuxi Data Provider")
    # info.set("Monitor9", "url", "36.155.95.59:28080/JKS_Server/SysInfo")
    # info.set("Monitor9", "type", "GET")
    # info.set("Monitor9", "format", "JSON")
    # info.set("Monitor9", "interval", "900")
    # info.set("Monitor9", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor10")
    # info.set("Monitor10", "name", "CN01-CN02")
    # info.set("Monitor10", "url", "219.239.83.74")
    # info.set("Monitor10", "type", "SERVER")
    # info.set("Monitor10", "format", "HTTP")
    # info.set("Monitor10", "interval", "900")
    # info.set("Monitor10", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor11")
    # info.set("Monitor11", "name", "Wuxi Live Target")
    # info.set(
    #     "Monitor11", "url",
    #     "101.42.254.16:6265/PSA/Services/GetLiveTargets?region=China.Wuxi&format=XML&filter=All"
    # )
    # info.set("Monitor11", "type", "GET")
    # info.set("Monitor11", "format", "XML")
    # info.set("Monitor11", "interval", "900")
    # info.set("Monitor11", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor12")
    # info.set("Monitor12", "name", "Nanjing-live Live Target")
    # info.set(
    #     "Monitor12", "url",
    #     "49.232.78.244:6265/PSA/Services/GetLiveTargets?region=China.Nanjing&format=XML&filter=All"
    # )
    # info.set("Monitor12", "type", "GET")
    # info.set("Monitor12", "format", "XML")
    # info.set("Monitor12", "interval", "900")
    # info.set("Monitor12", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor13")
    # info.set("Monitor13", "name", "Nanjing-lab Live Target")
    # info.set(
    #     "Monitor13", "url",
    #     "101.42.254.16:6265/PSA/Services/GetLiveTargets?region=China.Nanjing&format=XML&filter=All"
    # )
    # info.set("Monitor13", "type", "GET")
    # info.set("Monitor13", "format", "XML")
    # info.set("Monitor13", "interval", "900")
    # info.set("Monitor13", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor14")
    # info.set("Monitor14", "name", "Wuhan Live Target")
    # info.set(
    #     "Monitor14", "url",
    #     "49.233.41.147:6265/PSA/Services/GetLiveTargets?region=China.Wuhan&format=XML&filter=All"
    # )
    # info.set("Monitor14", "type", "GET")
    # info.set("Monitor14", "format", "XML")
    # info.set("Monitor14", "interval", "900")
    # info.set("Monitor14", "email", "johnnyzhao56192@gmail.com")

    # info.add_section("Monitor15")
    # info.set("Monitor15", "name", "Beijing Live Target")
    # info.set(
    #     "Monitor15", "url",
    #     "49.233.41.147:6265/PSA/Services/GetLiveTargets?region=China.Beijing&format=XML&filter=All"
    # )
    # info.set("Monitor15", "type", "GET")
    # info.set("Monitor15", "format", "XML")
    # info.set("Monitor15", "interval", "900")
    # info.set("Monitor15", "email", "johnnyzhao56192@gmail.com")
    info.write(open(os.path.join(config_dir, "MonitorList.ini"), "w"))


def save_general(app_name: str, version: str, timezone: str,
                 log_level: str) -> None:
    cfg = _read_config('Config.ini')
    if not cfg.has_section('General'):
        cfg.add_section('General')
    cfg.set('General', 'app_name', app_name or 'API Monitor')
    cfg.set('General', 'version', version or '1.3')
    if not cfg.has_section('Logging'):
        cfg.add_section('Logging')
    cfg.set('Logging', 'log_level', log_level or 'info')
    cfg.set('Logging', 'log_file', cfg.get('Logging', 'log_file',
                                           fallback='./API Monitor/'))
    if not cfg.has_section('TimeZone'):
        cfg.add_section('TimeZone')
    cfg.set('TimeZone', 'timezone', timezone)
    with open(_config_path("Config", "Config.ini"), "w") as f:
        cfg.write(f)


def save_mail(smtp_server: str, smtp_port: str, username: str, password: str,
              from_addr: str) -> None:
    cfg = _read_config('Config.ini')
    if not cfg.has_section('Mail'):
        cfg.add_section('Mail')
    cfg.set('Mail', 'smtp_server', smtp_server)
    cfg.set('Mail', 'smtp_port', smtp_port)
    cfg.set('Mail', 'username', username)
    cfg.set('Mail', 'password', password)
    cfg.set('Mail', 'from_addr', from_addr)
    with open(_config_path("Config", "Config.ini"), "w") as f:
        cfg.write(f)


def save_templates(outage_subject: str, outage_body: str,
                   restored_subject: str, restored_body: str,
                   log_line: str) -> None:
    cfg = _read_config('Config.ini')
    if not cfg.has_section(TEMPLATE_SECTION):
        cfg.add_section(TEMPLATE_SECTION)
    cfg.set(TEMPLATE_SECTION, 'outage_subject', outage_subject)
    cfg.set(TEMPLATE_SECTION, 'outage_body', outage_body)
    cfg.set(TEMPLATE_SECTION, 'restored_subject', restored_subject)
    cfg.set(TEMPLATE_SECTION, 'restored_body', restored_body)
    cfg.set(TEMPLATE_SECTION, 'log_line', log_line)
    with open(_config_path("Config", "Config.ini"), "w") as f:
        cfg.write(f)


def save_monitor_list(monitors: list) -> None:
    info = configparser.ConfigParser()
    info.add_section("MonitorNum")
    info.set("MonitorNum", "total", str(len(monitors)))
    for idx, item in enumerate(monitors, start=1):
        sec = f"Monitor{idx}"
        info.add_section(sec)
        info.set(sec, "name", item.get('name', ''))
        info.set(sec, "url", item.get('url', ''))
        info.set(sec, "type", item.get('type', 'GET'))
        info.set(sec, "format", item.get('format', 'HTTP'))
        info.set(sec, "interval", str(item.get('interval', 60)))
        info.set(sec, "email", item.get('email', ''))
        payload = item.get('payload', '')
        if payload != '':
            info.set(sec, "payload", payload)
        headers = item.get('headers', {})
        info.set(sec, "headers", json.dumps(headers))
    with open(_config_path("Config", "MonitorList.ini"), "w") as f:
        info.write(f)
