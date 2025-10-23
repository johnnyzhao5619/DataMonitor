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
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union


LOGGER = logging.getLogger(__name__)


MAIL_ENV_PREFIX = "MAIL_"
MAIL_ENV_MAP = {
    "smtp_server": f"{MAIL_ENV_PREFIX}SMTP_SERVER",
    "smtp_port": f"{MAIL_ENV_PREFIX}SMTP_PORT",
    "username": f"{MAIL_ENV_PREFIX}USERNAME",
    "password": f"{MAIL_ENV_PREFIX}PASSWORD",
    "from_addr": f"{MAIL_ENV_PREFIX}FROM",
    "to_addrs": f"{MAIL_ENV_PREFIX}TO",
    "use_starttls": f"{MAIL_ENV_PREFIX}USE_STARTTLS",
    "use_ssl": f"{MAIL_ENV_PREFIX}USE_SSL",
}
MAIL_BOOL_OPTIONS = frozenset({"use_starttls", "use_ssl"})
_BOOL_TRUE_VALUES = {"1", "true", "yes", "on"}
_BOOL_FALSE_VALUES = {"0", "false", "no", "off"}
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

DEFAULT_LANGUAGE = "zh_CN"

PREFERENCES_SECTION = "Preferences"
THEME_OPTION = "theme"
THEME_DISPLAY_NAME_OPTION = "theme_display_name"
THEME_DESCRIPTION_OPTION = "theme_description"
THEME_HIGH_CONTRAST_OPTION = "theme_high_contrast"
TIMEZONE_SECTION = "TimeZone"
TIMEZONE_OPTION = "timezone"

class TemplateResource:
    """描述模版使用的翻译资源。"""

    __slots__ = ("context", "source")

    def __init__(self, context: str, source: str) -> None:
        if not context or not source:
            raise ValueError("模版资源必须同时提供上下文与源文本")
        self.context = context
        self.source = source

    def __repr__(self) -> str:  # pragma: no cover - 调试辅助
        return f"TemplateResource(context={self.context!r}, source={self.source!r})"


def _i18n_root() -> Path:
    return Path(__file__).resolve().parent / "i18n"


@lru_cache(maxsize=1)
def _load_catalog_payload() -> dict[str, Any]:
    catalog_path = _i18n_root() / "catalog.json"
    if not catalog_path.is_file():
        raise RuntimeError(f"缺少翻译 catalog：{catalog_path}")
    with catalog_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError("catalog.json 格式错误：顶层必须是对象")
    return payload


def _load_catalog_languages() -> Tuple[str, ...]:
    payload = _load_catalog_payload()
    languages = payload.get("languages")
    if not isinstance(languages, list) or not languages:
        raise RuntimeError("catalog.json 缺少 languages 配置")
    normalised = [str(language) for language in languages if str(language).strip()]
    if not normalised:
        raise RuntimeError("catalog.json 未定义有效的语言列表")
    return tuple(sorted(dict.fromkeys(normalised)))


SUPPORTED_LANGUAGES = _load_catalog_languages()
if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
    raise RuntimeError(
        f"默认语言 {DEFAULT_LANGUAGE} 未包含在 catalog 的 languages 中"
    )
LANGUAGE_SECTION = "Locale"
LANGUAGE_OPTION = "language"

_LANGUAGE_CACHE: Optional[str] = None


_CONFIG_TEMPLATE_CREATED = False


_TEMPLATE_SECTION_PATTERN = re.compile(r"^(?P<category>[^\[]+?)(?:\[(?P<language>[^\]]+)\])?$")


@lru_cache(maxsize=None)
def _load_language_messages(language: str) -> Dict[str, Dict[str, str]]:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"不支持的语言：{language}")
    path = _i18n_root() / f"{language}.qm.json"
    if not path.is_file():
        raise RuntimeError(f"缺少翻译文件：{path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    messages = payload.get("messages")
    if not isinstance(messages, dict):
        raise RuntimeError(f"翻译文件 {path} 格式无效")
    normalised: Dict[str, Dict[str, str]] = {}
    for context, entries in messages.items():
        if not isinstance(entries, dict):
            continue
        normalised[str(context)] = {str(source): str(target) for source, target in entries.items()}
    return normalised


def _resolve_template_resource(resource: TemplateResource, language: str) -> str:
    translations = _load_language_messages(language)
    context_messages = translations.get(resource.context, {})
    if resource.source not in context_messages:
        raise KeyError(
            f"缺少模版翻译：{resource.context} -> {resource.source} ({language})"
        )
    return context_messages[resource.source]


TEMPLATE_DEFAULTS: Dict[str, Dict[str, TemplateResource]] = {
    "mail": {
        "alert_subject": TemplateResource(
            "Template.mail", "Outage Alert | {service_name}"
        ),
        "alert_body": TemplateResource(
            "Template.mail",
            (
                "Status: {status_action}\n"
                "Service: {service_name}\n"
                "Details: {event_description}\n"
                "{time_label}: {event_timestamp}"
            ),
        ),
        "recovery_subject": TemplateResource(
            "Template.mail", "Outage Recovery | {service_name}"
        ),
        "recovery_body": TemplateResource(
            "Template.mail",
            (
                "Status: {status_action}\n"
                "Service: {service_name}\n"
                "Details: {event_description}\n"
                "{time_label}: {event_timestamp}"
            ),
        ),
    },
    "ui": {
        "status_line": TemplateResource(
            "Template.ui",
            "Time: {event_timestamp} --> Status: {service_name}{status_label}",
        ),
    },
    "log": {
        "action_line": TemplateResource(
            "Template.log",
            "{service_name} --- Type: {monitor_type} --- URL: {url} --- Interval: {interval}s",
        ),
        "detail_line": TemplateResource(
            "Template.log",
            ">>>{event_timestamp}: {service_name}{status_label}",
        ),
        "record_entry": TemplateResource(
            "Template.log",
            (
                ">>{log_timestamp}(Local Time)----------------------------------------------\n"
                ">>Action:{action}\n"
                "{details}"
            ),
        ),
        "csv_header": TemplateResource(
            "Template.log", "Time,API,Type,url,Interval,Code,Status"
        ),
    },
}


def _materialise_template_defaults(language: str) -> Dict[str, Dict[str, str]]:
    """将 ``TEMPLATE_DEFAULTS`` 渲染为指定语言的纯文本模版。"""

    language_code = _validate_language_code(language)
    resolved: Dict[str, Dict[str, str]] = {}
    for category, entries in TEMPLATE_DEFAULTS.items():
        category_key = category.strip()
        if not category_key:
            continue
        rendered: Dict[str, str] = {}
        for key, resource in entries.items():
            key_name = key.strip()
            if not key_name:
                continue
            if isinstance(resource, TemplateResource):
                rendered[key_name] = _resolve_template_resource(resource, language_code)
            else:  # pragma: no cover - 为向后兼容保留
                rendered[key_name] = str(resource)
        if rendered:
            resolved[category_key] = rendered
    return resolved


class TemplateManager:
    """负责加载与渲染通知模版。"""

    def __init__(self):
        self._templates: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None

    def _load_templates(self) -> bool:
        templates: Dict[str, Dict[str, Dict[str, str]]] = {}
        for language in SUPPORTED_LANGUAGES:
            language_templates: Dict[str, Dict[str, str]] = {}
            for category, entries in TEMPLATE_DEFAULTS.items():
                category_key = category.strip().lower()
                resolved: Dict[str, str] = {}
                for key, resource in entries.items():
                    if isinstance(resource, TemplateResource):
                        resolved[key] = _resolve_template_resource(resource, language)
                    else:  # pragma: no cover - 向后兼容
                        resolved[key] = str(resource)
                language_templates[category_key] = resolved
            templates[language] = language_templates

        config_dir = get_config_directory()
        config_path = config_dir / TEMPLATE_CONFIG_NAME

        parser = configparser.RawConfigParser()
        parser.optionxform = str  # 保留键大小写

        load_failed = False

        if config_path.is_file():
            try:
                parser.read(os.fspath(config_path), encoding="utf-8")
            except (configparser.Error, OSError) as exc:
                load_failed = True
                LOGGER.warning(
                    "模板配置文件 %s 读取失败，将使用内置模板：%s", config_path, exc
                )
            else:
                for section in parser.sections():
                    match = _TEMPLATE_SECTION_PATTERN.match(section.strip())
                    if not match:
                        continue
                    category_key = (match.group("category") or "").strip().lower()
                    language_key = (match.group("language") or DEFAULT_LANGUAGE).strip()
                    if not category_key or not language_key:
                        continue
                    section_templates = templates.setdefault(language_key, {}).setdefault(
                        category_key, {}
                    )
                    for option, value in parser.items(section):
                        option_key = option.strip()
                        if not option_key:
                            continue
                        section_templates[option_key] = value

        self._templates = templates
        return not load_failed

    def get_template(self, category: str, key: str, language: Optional[str] = None) -> str:
        if self._templates is None:
            self._load_templates()

        category_key = category.strip().lower()
        key_name = key.strip()
        if not category_key or not key_name:
            raise KeyError(f"模板缺失：{category}.{key}")

        requested_language = language or get_language()
        candidate_languages = []
        if requested_language:
            candidate_languages.append(requested_language)
        if DEFAULT_LANGUAGE not in candidate_languages:
            candidate_languages.append(DEFAULT_LANGUAGE)

        for lang in candidate_languages:
            language_templates = self._templates.get(lang, {})
            category_templates = language_templates.get(category_key)
            if category_templates and key_name in category_templates:
                return category_templates[key_name]

        raise KeyError(f"模板缺失：{category}.{key}")

    def reload(self) -> bool:
        """在测试或配置更新后重新加载模版。"""

        self._templates = None
        return self._load_templates()


@lru_cache(maxsize=1)
def get_template_manager() -> TemplateManager:
    return TemplateManager()


def render_template(
    category: str,
    key: str,
    context: Mapping[str, object],
    *,
    language: Optional[str] = None,
) -> str:
    """渲染指定类别与键的模版。"""

    template = get_template_manager().get_template(category, key, language)
    try:
        return template.format(**context)
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(
            f"模板 {category}.{key} 渲染时缺少变量：{missing}"
        ) from exc


def available_languages() -> Tuple[str, ...]:
    return SUPPORTED_LANGUAGES


def get_language() -> str:
    global _LANGUAGE_CACHE
    if _LANGUAGE_CACHE is None:
        _LANGUAGE_CACHE = _load_language_setting()
    return _LANGUAGE_CACHE


def set_language(language: str) -> None:
    language_code = _validate_language_code(language)
    previous_language = get_language()

    parser, config_path = _load_config_parser(ensure_dir=True)
    changed = _set_config_value(parser, LANGUAGE_SECTION, LANGUAGE_OPTION, language_code)
    if changed or not config_path.exists():
        _write_config_parser(parser, config_path)

    _update_language_cache(language_code, previous_language)


def _load_language_setting() -> str:
    config_path = _config_file_path()
    parser = configparser.RawConfigParser()
    read_files = parser.read(os.fspath(config_path))
    if not read_files:
        return DEFAULT_LANGUAGE

    if not parser.has_section(LANGUAGE_SECTION):
        return DEFAULT_LANGUAGE

    value = parser.get(LANGUAGE_SECTION, LANGUAGE_OPTION, fallback=None)
    if not value:
        return DEFAULT_LANGUAGE

    value = value.strip()
    if not value:
        return DEFAULT_LANGUAGE
    if value not in SUPPORTED_LANGUAGES:
        return DEFAULT_LANGUAGE
    return value


def _config_file_path() -> Path:
    return Path(get_logdir()) / "Config" / "Config.ini"


def _load_config_parser(*, ensure_dir: bool = False) -> Tuple[configparser.RawConfigParser, Path]:
    config_path = _config_file_path()
    if ensure_dir:
        config_path.parent.mkdir(parents=True, exist_ok=True)

    parser = configparser.RawConfigParser()
    if config_path.exists():
        parser.read(os.fspath(config_path))
    return parser, config_path


def _write_config_parser(parser: configparser.RawConfigParser, path: Path) -> None:
    with path.open("w") as configfile:
        parser.write(configfile)


def _set_config_value(
    parser: configparser.RawConfigParser,
    section: str,
    option: str,
    value: Optional[str],
) -> bool:
    if value is None:
        if not parser.has_section(section):
            return False
        removed = parser.remove_option(section, option)
        if removed and not parser.items(section):
            parser.remove_section(section)
        return removed

    text = str(value)
    if not parser.has_section(section):
        parser.add_section(section)
    current = parser.get(section, option, fallback=None)
    if current == text:
        return False
    parser.set(section, option, text)
    return True


def _validate_language_code(language: object) -> str:
    language_code = str(language).strip()
    if not language_code:
        raise ValueError("语言代码不能为空")
    if language_code not in SUPPORTED_LANGUAGES:
        raise ValueError(f"不支持的语言：{language_code}")
    return language_code


def _update_language_cache(new_code: str, previous: Optional[str]) -> None:
    global _LANGUAGE_CACHE
    if previous != new_code:
        _LANGUAGE_CACHE = new_code
        get_template_manager().reload()
    else:
        _LANGUAGE_CACHE = new_code


def _normalise_timezone_value(value: object) -> str:
    timezone_text = str(value).strip()
    if not timezone_text:
        raise ValueError("时区值不能为空")
    try:
        int(timezone_text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"无效的时区值：{value}") from exc
    return timezone_text


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


def _ensure_templates_file(config_dir: Path) -> bool:
    """确保模版配置文件存在。

    返回值指示是否创建了新的示例模版文件。
    """

    templates_path = config_dir / TEMPLATE_CONFIG_NAME
    if templates_path.exists():
        return False

    config_dir.mkdir(parents=True, exist_ok=True)

    parser = configparser.RawConfigParser()
    parser.optionxform = str

    default_templates = _materialise_template_defaults(DEFAULT_LANGUAGE)
    for category, entries in sorted(default_templates.items()):
        parser.add_section(category)
        for key, value in sorted(entries.items()):
            parser.set(category, key, value)

    for language in SUPPORTED_LANGUAGES:
        if language == DEFAULT_LANGUAGE:
            continue
        language_templates = _materialise_template_defaults(language)
        for category, entries in sorted(language_templates.items()):
            section_name = f"{category}[{language}]"
            parser.add_section(section_name)
            for key, value in sorted(entries.items()):
                parser.set(section_name, key, value)

    header_lines = [
        "; 此文件由系统自动生成，展示当前可用模版键的默认内容。",
        f"; [类别] 节表示 {DEFAULT_LANGUAGE} 语言的默认文本。",
        "; 若需覆盖其它语言，请新增 [类别[语言代码]] 节并复制所需键进行修改。",
        "; 例如：在 [mail[en_US]] 中自定义邮件模版。",
        "; 删除某个键即可回退到内置默认模版。",
    ]

    with templates_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(header_lines))
        handle.write("\n\n")
        parser.write(handle)

    return True

def read_monitor_list() -> List[MonitorItem]:
    global _CONFIG_TEMPLATE_CREATED

    config_path = _config_file_path()
    config_dir = config_path.parent
    config_created = False

    if not config_path.exists():
        try:
            writeconfig(str(config_dir))
        except Exception as exc:  # pragma: no cover - 非预期错误
            LOGGER.error("初始配置生成失败: %s", exc)
            return []

        config_created = True

    template_created = False
    try:
        template_created = _ensure_templates_file(config_dir)
    except Exception as exc:  # pragma: no cover - 防御性日志
        LOGGER.error("模版文件生成失败: %s", exc)

    if config_created:
        _CONFIG_TEMPLATE_CREATED = True
        LOGGER.info("配置文件缺失，已在 %s 生成示例模板", config_path)
    elif template_created:
        _CONFIG_TEMPLATE_CREATED = True
        LOGGER.info(
            "模版文件缺失，已在 %s 生成示例模版", config_dir / TEMPLATE_CONFIG_NAME
        )

    parser, _ = _load_config_parser()
    monitorlist: List[MonitorItem] = []

    try:
        total_number = parser.getint("MonitorNum", "total")
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        LOGGER.error("缺少 MonitorNum.total 配置或值无效")
        return monitorlist

    for index in range(total_number):
        section_name = f"Monitor{index + 1}"
        try:
            monitor = _build_monitor_item(parser, section_name)
        except ValueError as exc:
            LOGGER.error("监控项 %s 解析失败: %s", section_name, exc)
            continue

        monitorlist.append(monitor)

    if config_created or template_created:
        get_template_manager().reload()

    return monitorlist


def consume_config_template_created_flag() -> bool:
    """返回并清除示例配置创建标记。"""

    global _CONFIG_TEMPLATE_CREATED
    created = _CONFIG_TEMPLATE_CREATED
    _CONFIG_TEMPLATE_CREATED = False
    return created


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
    return parse_mapping_string(raw_value)


def parse_mapping_string(raw_value: Optional[str]):
    """解析映射字符串，支持 JSON 或 key=value 对列表。"""

    if raw_value is None:
        return None

    text = str(raw_value).strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = _parse_key_value_pairs(text)
    else:
        if not isinstance(parsed, dict):
            raise ValueError("映射内容必须为 JSON 对象")
    return parsed


def _prepare_mapping_for_write(value):
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    raise TypeError("映射值必须为 dict 或字符串")


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

    config_paths = [
        _config_file_path(),
        Path("config.ini"),
    ]

    for path in config_paths:
        path_obj = Path(path)
        if not path_obj.is_file():
            continue
        config = configparser.RawConfigParser()
        config.read(os.fspath(path_obj))
        if config.has_option(REQUEST_SECTION, REQUEST_TIMEOUT_KEY):
            timeout_value = config.getfloat(REQUEST_SECTION, REQUEST_TIMEOUT_KEY)
            if timeout_value <= 0:
                raise ValueError(
                    f"配置文件 {path_obj} 中的 {REQUEST_SECTION}.{REQUEST_TIMEOUT_KEY} 必须为正数"
                )
            return timeout_value

    return DEFAULT_REQUEST_TIMEOUT


def reset_request_timeout_cache() -> float:
    """清空请求超时的缓存，并返回刷新后的最新值。"""

    cache_clear = getattr(get_request_timeout, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()
    return get_request_timeout()

def read_mail_configuration():
    """读取邮件配置，优先使用环境变量，其次使用外部配置文件，最后回退到项目配置。"""

    mailconfig = _load_mail_config_from_env()
    if mailconfig:
        return mailconfig

    mailconfig = _load_mail_config_from_external_file()
    if mailconfig:
        return mailconfig

    return _load_mail_config_from_project_file()


def _coerce_mail_bool(value: Any, *, key: str, source: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalised = value.strip().lower()
        if normalised in _BOOL_TRUE_VALUES:
            return True
        if normalised in _BOOL_FALSE_VALUES:
            return False
    raise ValueError(f"{source} 的 {key} 不是有效的布尔值：{value!r}")


def _normalise_mail_values(values: Mapping[str, Any], *, source: str) -> Dict[str, Any]:
    normalised: Dict[str, Any] = {}
    for key in MAIL_ENV_MAP:
        if key not in values:
            raise ValueError(f"{source} 缺少邮件配置字段：{key}")
        value = values[key]
        if key in MAIL_BOOL_OPTIONS:
            normalised[key] = _coerce_mail_bool(value, key=key, source=source)
        else:
            normalised[key] = value
    return normalised


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
        return _normalise_mail_values(values, source="环境变量")

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

    return _normalise_mail_values(values, source=f"外部配置文件 {path}")


def _load_mail_config_from_project_file():
    config_path = _config_file_path()
    if not config_path.exists():
        writeconfig(str(config_path.parent))

    config = configparser.RawConfigParser()
    config.read(os.fspath(config_path))

    if not config.has_section(MAIL_SECTION):
        raise ValueError(
            f"项目配置缺少 [{MAIL_SECTION}] 配置节：{os.fspath(config_path)}"
        )

    values = {key: config.get(MAIL_SECTION, key, fallback=None) for key in MAIL_ENV_MAP}
    missing_keys = [key for key, value in values.items() if not value]
    if missing_keys:
        raise ValueError(
            "项目配置文件缺少以下邮件配置字段：{}".format(
                ", ".join(missing_keys)
            )
        )

    return _normalise_mail_values(values, source=f"项目配置文件 {os.fspath(config_path)}")


def get_timezone():
    parser, config_path = _load_config_parser()

    if not config_path.exists():
        LOGGER.warning("未找到时区配置文件 %s，使用默认值 %s", config_path, DEFAULT_TIMEZONE)
        return DEFAULT_TIMEZONE

    if not parser.has_section(TIMEZONE_SECTION):
        LOGGER.warning(
            "配置文件 %s 缺少 [%s] 节，使用默认值 %s",
            config_path,
            TIMEZONE_SECTION,
            DEFAULT_TIMEZONE,
        )
        return DEFAULT_TIMEZONE

    if not parser.has_option(TIMEZONE_SECTION, TIMEZONE_OPTION):
        LOGGER.warning(
            "配置文件 %s 缺少 [%s].%s，使用默认值 %s",
            config_path,
            TIMEZONE_SECTION,
            TIMEZONE_OPTION,
            DEFAULT_TIMEZONE,
        )
        return DEFAULT_TIMEZONE

    timezone_value = parser.get(TIMEZONE_SECTION, TIMEZONE_OPTION, fallback=None)
    if timezone_value is None:
        LOGGER.warning(
            "配置文件 %s 的 [%s].%s 为空，使用默认值 %s",
            config_path,
            TIMEZONE_SECTION,
            TIMEZONE_OPTION,
            DEFAULT_TIMEZONE,
        )
        return DEFAULT_TIMEZONE

    timezone_value = timezone_value.strip()
    if not timezone_value:
        LOGGER.warning(
            "配置文件 %s 的 [%s].%s 为空字符串，使用默认值 %s",
            config_path,
            TIMEZONE_SECTION,
            TIMEZONE_OPTION,
            DEFAULT_TIMEZONE,
        )
        return DEFAULT_TIMEZONE

    return timezone_value


def set_timezone(timezone):
    timezone_value = _normalise_timezone_value(timezone)
    parser, config_path = _load_config_parser(ensure_dir=True)
    changed = _set_config_value(parser, TIMEZONE_SECTION, TIMEZONE_OPTION, timezone_value)
    if changed or not config_path.exists():
        _write_config_parser(parser, config_path)


def get_preferences() -> Dict[str, Optional[str]]:
    parser, _ = _load_config_parser()

    theme_value: Optional[str] = None
    theme_display: Optional[str] = None
    theme_description: Optional[str] = None
    theme_high_contrast = False
    if parser.has_section(PREFERENCES_SECTION):
        raw_theme = parser.get(PREFERENCES_SECTION, THEME_OPTION, fallback=None)
        if raw_theme is not None:
            stripped = raw_theme.strip()
            theme_value = stripped or None
        raw_display = parser.get(
            PREFERENCES_SECTION, THEME_DISPLAY_NAME_OPTION, fallback=None
        )
        if raw_display is not None:
            stripped = raw_display.strip()
            theme_display = stripped or None
        raw_description = parser.get(
            PREFERENCES_SECTION, THEME_DESCRIPTION_OPTION, fallback=None
        )
        if raw_description is not None:
            stripped = raw_description.strip()
            theme_description = stripped or None
        raw_contrast = parser.get(
            PREFERENCES_SECTION, THEME_HIGH_CONTRAST_OPTION, fallback=None
        )
        if raw_contrast is not None:
            theme_high_contrast = _parse_bool(raw_contrast)

    return {
        "theme": theme_value,
        "theme_display_name": theme_display,
        "theme_description": theme_description,
        "theme_high_contrast": theme_high_contrast,
        "language": get_language(),
        "timezone": get_timezone(),
    }


def _parse_bool(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "on"}


def set_preferences(preferences: Mapping[str, object]) -> None:
    if not isinstance(preferences, Mapping):
        raise TypeError("偏好设置必须为映射类型")

    parser, config_path = _load_config_parser(ensure_dir=True)
    changed = False

    def _remove_preference_option(option: str) -> None:
        nonlocal changed
        if not parser.has_section(PREFERENCES_SECTION):
            return
        removed = parser.remove_option(PREFERENCES_SECTION, option)
        if removed:
            changed = True
            if not parser.items(PREFERENCES_SECTION):
                parser.remove_section(PREFERENCES_SECTION)

    def _set_text_option(option: str, value: object) -> None:
        nonlocal changed
        if value is None:
            _remove_preference_option(option)
            return
        text = str(value).strip()
        if not text:
            _remove_preference_option(option)
            return
        if _set_config_value(parser, PREFERENCES_SECTION, option, text):
            changed = True

    def _set_bool_option(option: str, value: object) -> None:
        nonlocal changed
        if value is None:
            _remove_preference_option(option)
            return
        text = "true" if _parse_bool(value) else "false"
        if _set_config_value(parser, PREFERENCES_SECTION, option, text):
            changed = True

    language_code: Optional[str] = None
    previous_language: Optional[str] = None
    if "language" in preferences:
        previous_language = get_language()
        language_code = _validate_language_code(preferences["language"])
        if _set_config_value(parser, LANGUAGE_SECTION, LANGUAGE_OPTION, language_code):
            changed = True

    if "timezone" in preferences:
        timezone_value = _normalise_timezone_value(preferences["timezone"])
        if _set_config_value(parser, TIMEZONE_SECTION, TIMEZONE_OPTION, timezone_value):
            changed = True

    if "theme" in preferences:
        theme_value = preferences["theme"]
        theme_text = None
        if theme_value is not None:
            theme_text = str(theme_value).strip()
        if theme_text:
            if _set_config_value(parser, PREFERENCES_SECTION, THEME_OPTION, theme_text):
                changed = True
        else:
            _remove_preference_option(THEME_OPTION)
            _remove_preference_option(THEME_DISPLAY_NAME_OPTION)
            _remove_preference_option(THEME_DESCRIPTION_OPTION)
            _remove_preference_option(THEME_HIGH_CONTRAST_OPTION)

    if "theme_display_name" in preferences:
        _set_text_option(THEME_DISPLAY_NAME_OPTION, preferences["theme_display_name"])

    if "theme_description" in preferences:
        _set_text_option(THEME_DESCRIPTION_OPTION, preferences["theme_description"])

    if "theme_high_contrast" in preferences:
        _set_bool_option(
            THEME_HIGH_CONTRAST_OPTION, preferences["theme_high_contrast"]
        )

    if changed or not config_path.exists():
        _write_config_parser(parser, config_path)

    if language_code is not None:
        _update_language_cache(language_code, previous_language)


def write_monitor_list(monitors: List[Dict[str, object]]) -> None:
    """将监控项列表写入配置文件。"""

    config, config_path = _load_config_parser(ensure_dir=True)

    if not config.has_section("MonitorNum"):
        config.add_section("MonitorNum")

    for section in list(config.sections()):
        if section.lower().startswith("monitor") and section != "MonitorNum":
            config.remove_section(section)

    config.set("MonitorNum", "total", str(len(monitors)))

    for index, monitor in enumerate(monitors, start=1):
        section = f"Monitor{index}"
        config.add_section(section)

        name = str(monitor.get("name", "")).strip()
        url = str(monitor.get("url", "")).strip()
        monitor_type = str(monitor.get("type", "")).strip().upper()
        interval = int(monitor.get("interval", 0))
        email = str(monitor.get("email", "")).strip()

        if not name:
            raise ValueError(f"{section} 名称不能为空")
        if not url:
            raise ValueError(f"{section} URL 不能为空")
        if monitor_type not in SUPPORTED_MONITOR_TYPES:
            raise ValueError(
                f"{section} 类型必须为 {sorted(SUPPORTED_MONITOR_TYPES)} 之一"
            )
        if interval <= 0:
            raise ValueError(f"{section} 轮询周期必须为正整数")

        config.set(section, "name", name)
        config.set(section, "url", url)
        config.set(section, "type", monitor_type)
        config.set(section, "interval", str(interval))
        config.set(section, "email", email)

        payload_text = _prepare_mapping_for_write(monitor.get("payload"))
        headers_text = _prepare_mapping_for_write(monitor.get("headers"))
        if payload_text:
            config.set(section, "payload", payload_text)
        if headers_text:
            config.set(section, "headers", headers_text)

    _write_config_parser(config, config_path)




def writeconfig(configDir: str) -> None:
    config_dir = Path(configDir).expanduser()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file_path = config_dir / "Config.ini"

    info = configparser.ConfigParser()
    info.add_section("General")
    info.set("General", "app_name", "Monitor Everything")
    info.set("General", "version", "1.0")

    info.add_section("Logging")
    info.set("Logging", "log_level", "info")
    log_root = config_dir.parent
    info.set("Logging", "log_file", _normalise_directory(log_root))

    info.add_section(TIMEZONE_SECTION)
    info.set(TIMEZONE_SECTION, TIMEZONE_OPTION, DEFAULT_TIMEZONE)

    info.add_section(LANGUAGE_SECTION)
    info.set(LANGUAGE_SECTION, LANGUAGE_OPTION, DEFAULT_LANGUAGE)

    mail_placeholders = {
        "smtp_server": "<SMTP_SERVER>",
        "smtp_port": "<SMTP_PORT>",
        "username": "<USERNAME>",
        "password": "<PASSWORD>",
        "from_addr": "<FROM_ADDRESS>",
        "to_addrs": "<TO_ADDRESSES>",
        "use_starttls": "false",
        "use_ssl": "false",
        "subject": "Outage Alert",
    }
    info.add_section(MAIL_SECTION)
    for option, value in mail_placeholders.items():
        info.set(MAIL_SECTION, option, value)

    info.add_section("MonitorNum")
    info.set("MonitorNum", "total", "0")

    with config_file_path.open("w", encoding="utf-8") as config_file:
        info.write(config_file)

    _ensure_templates_file(config_dir)
