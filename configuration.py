# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 4:14 p.m.
# @Author: weijiazhao
# @File : configuration.py
# @Software: PyCharm
import configparser
import os
from pathlib import Path


MAIL_ENV_PREFIX = "MAIL_"
MAIL_ENV_MAP = {
    "smtp_server": f"{MAIL_ENV_PREFIX}SMTP_SERVER",
    "smtp_port": f"{MAIL_ENV_PREFIX}SMTP_PORT",
    "username": f"{MAIL_ENV_PREFIX}USERNAME",
    "password": f"{MAIL_ENV_PREFIX}PASSWORD",
    "from_addr": f"{MAIL_ENV_PREFIX}FROM",
    "to_addrs": f"{MAIL_ENV_PREFIX}TO",
}
MAIL_SECTION = "Mail"
EXTERNAL_MAIL_CONFIG_ENV = "MAIL_CONFIG_PATH"


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
    """读取邮件配置，优先使用环境变量，其次使用外部配置文件，最后回退到项目配置。"""

    mailconfig = _load_mail_config_from_env()
    if mailconfig:
        return mailconfig

    mailconfig = _load_mail_config_from_external_file()
    if mailconfig:
        return mailconfig

    return _load_mail_config_from_project_file()


def _load_mail_config_from_env():
    values = {}
    missing_keys = []
    for key, env_name in MAIL_ENV_MAP.items():
        value = os.environ.get(env_name)
        if value:
            values[key] = value
        else:
            missing_keys.append(key)

    if values and missing_keys:
        raise ValueError(
            "环境变量缺少以下邮件配置字段：{}".format(
                ", ".join(missing_keys)
            )
        )

    if values:
        return values

    return None


def _load_mail_config_from_external_file():
    config_path = os.environ.get(EXTERNAL_MAIL_CONFIG_ENV)
    if not config_path:
        return None

    path = Path(config_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"指定的邮件配置文件不存在：{path}")

    config = configparser.RawConfigParser()
    config.read(path)

    if not config.has_section(MAIL_SECTION):
        raise ValueError(f"外部配置文件缺少 [{MAIL_SECTION}] 配置节：{path}")

    values = {key: config.get(MAIL_SECTION, key, fallback=None) for key in MAIL_ENV_MAP}
    missing_keys = [key for key, value in values.items() if not value]
    if missing_keys:
        raise ValueError(
            "外部配置文件缺少以下邮件配置字段：{}".format(
                ", ".join(missing_keys)
            )
        )

    return values


def _load_mail_config_from_project_file():
    logdir = get_logdir()
    config = configparser.RawConfigParser()
    config.read(logdir + "Config/Config.ini")

    if not config.has_section(MAIL_SECTION):
        raise ValueError(f"项目配置缺少 [{MAIL_SECTION}] 配置节：{logdir}Config/Config.ini")

    values = {key: config.get(MAIL_SECTION, key, fallback=None) for key in MAIL_ENV_MAP}
    missing_keys = [key for key, value in values.items() if not value]
    if missing_keys:
        raise ValueError(
            "项目配置文件缺少以下邮件配置字段：{}".format(
                ", ".join(missing_keys)
            )
        )

    return values

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
    config.set('TimeZone', 'timezone', str(timezone))
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
    info.set("Mail", "smtp_server", "smtp.example.com")
    info.set("Mail", "smtp_port", "587")
    info.set("Mail", "username", "ops-team@example.com")
    info.set("Mail", "password", "PLEASE_SET_PASSWORD")
    info.set("Mail", "from_addr", "ops-team@example.com")
    info.set("Mail", "to_addrs", "recipient@example.com")
    info.set("Mail", "subject", "Outage Alert")

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

    with open('./APIMonitor/Config/Config.ini', 'w') as config_file:
        info.write(config_file)