# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 4:14 p.m.
# @Author: weijiazhao
# @File : configuration.py
# @Software: PyCharm
import configparser
import json
import logging
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Mapping, Optional, Union


LOGGER = logging.getLogger(__name__)


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
REQUEST_SECTION = "Request"
REQUEST_TIMEOUT_KEY = "timeout"
REQUEST_TIMEOUT_ENV = "REQUEST_TIMEOUT"
DEFAULT_REQUEST_TIMEOUT = 10.0


SUPPORTED_MONITOR_TYPES = frozenset({"GET", "POST", "SERVER"})


@dataclass(frozen=True)
class MonitorItem:
    """用于描述单个监控项的配置。"""

    name: str
    url: str
    monitor_type: str
    interval: int
    email: Optional[str] = None
    payload: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None

    def normalised_email(self) -> Optional[str]:
        if self.email:
            stripped = self.email.strip()
            return stripped or None
        return None


DEFAULT_TIMEZONE = "0"


LOG_DIR_ENV = "APIMONITOR_HOME"

TEMPLATE_CONFIG_NAME = "Templates.ini"

TEMPLATE_DEFAULTS: Dict[str, Dict[str, str]] = {
    "mail": {
        "alert_subject": "Outage Alert | {service_name}",
        "alert_body": (
            "状态：{status_action}\n"
            "服务：{service_name}\n"
            "说明：{event_description}\n"
            "{time_label}：{event_timestamp}"
        ),
        "recovery_subject": "Outage Recovery | {service_name}",
        "recovery_body": (
            "状态：{status_action}\n"
            "服务：{service_name}\n"
            "说明：{event_description}\n"
            "{time_label}：{event_timestamp}"
        ),
    },
    "ui": {
        "status_line": "时间：{event_timestamp} --> 状态：{service_name}{status_label}",
    },
    "log": {
        "action_line": (
            "{service_name} --- 类型 Type: {monitor_type} --- 地址 url: {url} --- 周期 Interval: {interval}秒"
        ),
        "detail_line": ">>>{event_timestamp}: {service_name}{status_label}",
        "record_entry": (
            ">>{log_timestamp}(China Time)----------------------------------------------\n"
            ">>Action:{action}\n"
            "{details}"
        ),
        "csv_header": "Time,API,Type,url,Interval,Code,Status",
    },
}


class TemplateManager:
    """负责加载与渲染通知模版。"""

    def __init__(self):
        self._templates: Optional[Dict[str, Dict[str, str]]] = None

    def _load_templates(self) -> None:
        templates: Dict[str, Dict[str, str]] = {
            category: values.copy() for category, values in TEMPLATE_DEFAULTS.items()
        }

        config_dir = get_config_directory()
        config_path = config_dir / TEMPLATE_CONFIG_NAME

        parser = configparser.RawConfigParser()
        parser.optionxform = str  # 保留键大小写

        if config_path.is_file():
            parser.read(os.fspath(config_path), encoding="utf-8")
            for section in parser.sections():
                section_key = section.strip().lower()
                if not section_key:
                    continue
                section_templates = templates.setdefault(section_key, {})
                for option, value in parser.items(section):
                    option_key = option.strip()
                    if not option_key:
                        continue
                    section_templates[option_key] = value

        self._templates = templates

    def get_template(self, category: str, key: str) -> str:
        if self._templates is None:
            self._load_templates()

        category_key = category.strip().lower()
        key_name = key.strip()
        try:
            category_templates = self._templates[category_key]
        except KeyError as exc:
            raise KeyError(f"未找到模板类别：{category}") from exc

        try:
            return category_templates[key_name]
        except KeyError as exc:
            raise KeyError(f"模板缺失：{category}.{key}") from exc

    def reload(self) -> None:
        """在测试或配置更新后重新加载模版。"""

        self._templates = None


@lru_cache(maxsize=1)
def get_template_manager() -> TemplateManager:
    return TemplateManager()


def render_template(category: str, key: str, context: Mapping[str, object]) -> str:
    """渲染指定类别与键的模版。"""

    template = get_template_manager().get_template(category, key)
    try:
        return template.format(**context)
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(
            f"模板 {category}.{key} 渲染时缺少变量：{missing}"
        ) from exc


def _normalise_directory(
    path_value: Union[str, os.PathLike[str], Path],
    *,
    base_dir: Optional[Path] = None,
) -> str:
    """将路径归一化为绝对形式，并确保以分隔符结尾。"""

    if path_value is None:
        raise ValueError("缺少目录路径值")

    path = Path(path_value).expanduser()
    if path.is_absolute():
        resolved = path.resolve()
    else:
        if base_dir is not None:
            base_path = Path(base_dir).expanduser().resolve()
            resolved = (base_path / path).resolve()
        else:
            resolved = path.resolve()

    normalised = str(resolved)
    if not normalised.endswith(os.sep):
        normalised += os.sep
    return normalised


def get_logdir():
    """返回日志根目录。

    优先级：
    1. 环境变量 ``APIMONITOR_HOME``；
    2. ``config.ini`` 与 ``APIMonitor/Config/Config.ini`` 中 ``[Logging].log_file`` 配置；
    3. 项目默认目录 ``APIMonitor``。
    """

    env_path = os.environ.get(LOG_DIR_ENV)
    if env_path:
        try:
            return _normalise_directory(env_path)
        except Exception as exc:  # pragma: no cover - 防御性日志
            LOGGER.warning("环境变量 %s 的值无效：%s", LOG_DIR_ENV, exc)

    candidate_configs = [
        Path("config.ini"),
        Path(__file__).resolve().parent / "APIMonitor" / "Config" / "Config.ini",
    ]

    for config_path in candidate_configs:
        if not config_path.is_file():
            continue

        config = configparser.RawConfigParser()
        resolved_path = config_path.resolve()
        config.read(os.fspath(resolved_path))
        if not config.has_option("Logging", "log_file"):
            continue

        raw_value = config.get("Logging", "log_file", fallback="").strip()
        if not raw_value:
            continue

        try:
            return _normalise_directory(raw_value, base_dir=resolved_path.parent)
        except Exception as exc:  # pragma: no cover - 防御性日志
            LOGGER.warning(
                "配置文件 %s 中的 [Logging].log_file 无法解析：%s",
                config_path,
                exc,
            )

    default_dir = Path(__file__).resolve().parent / "APIMonitor"
    return _normalise_directory(default_dir)


def get_config_directory() -> Path:
    """返回配置目录路径。"""

    return Path(get_logdir()).resolve() / "Config"

def read_monitor_list():
    logdir = get_logdir()
    monitorlist: List[MonitorItem] = []
    config = configparser.RawConfigParser()
    config.read(logdir + "Config/Config.ini")

    try:
        total_number = config.getint("MonitorNum", "total")
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        LOGGER.error("缺少 MonitorNum.total 配置或值无效")
        return monitorlist

    for i in range(total_number):
        section_name = f"Monitor{i + 1}"
        try:
            monitor = _build_monitor_item(config, section_name)
        except ValueError as exc:
            LOGGER.error("监控项 %s 解析失败: %s", section_name, exc)
            continue

        monitorlist.append(monitor)

    return monitorlist


def _build_monitor_item(config: configparser.RawConfigParser, section_name: str) -> MonitorItem:
    if not config.has_section(section_name):
        raise ValueError("缺少配置节")

    name = _require_non_empty(config, section_name, "name")
    url = _require_non_empty(config, section_name, "url")

    raw_type = _require_non_empty(config, section_name, "type").upper()
    if raw_type not in SUPPORTED_MONITOR_TYPES:
        raise ValueError(f"不支持的监控类型: {raw_type}")

    interval_value = _require_non_empty(config, section_name, "interval")
    try:
        interval = int(interval_value)
    except ValueError as exc:
        raise ValueError("interval 必须为整数") from exc
    if interval <= 0:
        raise ValueError("interval 必须为正数")

    email = config.get(section_name, "email", fallback=None)
    email = email.strip() if isinstance(email, str) else None
    if not email:
        email = None

    payload = _load_optional_payload(config, section_name)
    headers = _load_optional_headers(config, section_name)

    return MonitorItem(
        name=name,
        url=url,
        monitor_type=raw_type,
        interval=interval,
        email=email,
        payload=payload,
        headers=headers,
    )


def _require_non_empty(config: configparser.RawConfigParser, section: str, option: str) -> str:
    value = config.get(section, option, fallback="")
    if value is None:
        raise ValueError(f"{section}.{option} 不能为空")

    stripped = str(value).strip()
    if not stripped:
        raise ValueError(f"{section}.{option} 不能为空")
    return stripped


def _load_optional_payload(config: configparser.RawConfigParser, section: str):
    return _load_optional_mapping(config, section, "payload")


def _load_optional_headers(config: configparser.RawConfigParser, section: str):
    return _load_optional_mapping(config, section, "headers")


def _load_optional_mapping(config: configparser.RawConfigParser, section: str, option: str):
    if not config.has_option(section, option):
        return None

    raw_value = config.get(section, option, fallback="")
    if raw_value is None:
        return None

    raw_value = raw_value.strip()
    if not raw_value:
        return None

    # 首选 JSON 格式
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        parsed = _parse_key_value_pairs(raw_value)
    else:
        if not isinstance(parsed, dict):
            raise ValueError(f"{section}.{option} 需要为 JSON 对象或键值对")
    return parsed


def _parse_key_value_pairs(raw_value: str):
    pairs = {}
    segments = []
    for line in raw_value.splitlines():
        line = line.strip()
        if not line:
            continue
        segments.extend(
            sub.strip()
            for sub in re.split(r"[;,]", line)
            if sub.strip()
        )

    for segment in segments:
        if "=" in segment:
            key, value = segment.split("=", 1)
        elif ":" in segment:
            key, value = segment.split(":", 1)
        else:
            raise ValueError(f"无法解析键值对: '{segment}'")

        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError("键不能为空")
        pairs[key] = value

    if not pairs:
        raise ValueError("未解析到有效的键值对")

    return pairs


@lru_cache(maxsize=1)
def get_request_timeout():
    """返回请求超时时间，优先使用环境变量，其次读取配置文件，最后回退到默认值。"""

    env_timeout = os.environ.get(REQUEST_TIMEOUT_ENV)
    if env_timeout:
        try:
            timeout_value = float(env_timeout)
            if timeout_value <= 0:
                raise ValueError
            return timeout_value
        except ValueError as exc:
            raise ValueError(
                f"环境变量 {REQUEST_TIMEOUT_ENV} 的值无效，需为正数。"
            ) from exc

    config_paths = []
    logdir = get_logdir()
    config_paths.append(os.path.join(logdir, "Config", "Config.ini"))
    config_paths.append("config.ini")

    for path in config_paths:
        if not os.path.isfile(path):
            continue
        config = configparser.RawConfigParser()
        config.read(path)
        if config.has_option(REQUEST_SECTION, REQUEST_TIMEOUT_KEY):
            timeout_value = config.getfloat(REQUEST_SECTION, REQUEST_TIMEOUT_KEY)
            if timeout_value <= 0:
                raise ValueError(
                    f"配置文件 {path} 中的 {REQUEST_SECTION}.{REQUEST_TIMEOUT_KEY} 必须为正数"
                )
            return timeout_value

    return DEFAULT_REQUEST_TIMEOUT

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
    config_path = Path(logdir) / "Config" / "Config.ini"

    read_files = config.read(os.fspath(config_path))
    if not read_files:
        LOGGER.warning("未找到时区配置文件 %s，使用默认值 %s", config_path, DEFAULT_TIMEZONE)
        return DEFAULT_TIMEZONE

    if not config.has_section("TimeZone"):
        LOGGER.warning("配置文件 %s 缺少 [TimeZone] 节，使用默认值 %s", config_path, DEFAULT_TIMEZONE)
        return DEFAULT_TIMEZONE

    if not config.has_option("TimeZone", "timezone"):
        LOGGER.warning(
            "配置文件 %s 缺少 [TimeZone].timezone，使用默认值 %s",
            config_path,
            DEFAULT_TIMEZONE,
        )
        return DEFAULT_TIMEZONE

    timezone_value = config.get("TimeZone", "timezone", fallback=None)
    if timezone_value is None:
        LOGGER.warning(
            "配置文件 %s 的 [TimeZone].timezone 为空，使用默认值 %s",
            config_path,
            DEFAULT_TIMEZONE,
        )
        return DEFAULT_TIMEZONE

    timezone_value = timezone_value.strip()
    if not timezone_value:
        LOGGER.warning(
            "配置文件 %s 的 [TimeZone].timezone 为空字符串，使用默认值 %s",
            config_path,
            DEFAULT_TIMEZONE,
        )
        return DEFAULT_TIMEZONE

    return timezone_value

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
    config_path = Path(configDir).expanduser()
    config_path.mkdir(parents=True, exist_ok=True)
    config_file_path = config_path / "Config.ini"

    info = configparser.ConfigParser()
    info.add_section("General")
    info.set("General", "app_name", "Monitor Everything")
    info.set("General", "version", "0.2")

    info.add_section("Logging")
    info.set("Logging", "log_level", "info")
    log_root = config_path.parent
    info.set("Logging", "log_file", _normalise_directory(log_root))

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

    with config_file_path.open('w') as config_file:
        info.write(config_file)
