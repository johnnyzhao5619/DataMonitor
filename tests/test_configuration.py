import configparser
import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture(autouse=True)
def _reset_language_cache():
    original = configuration._LANGUAGE_CACHE
    original_template_flag = configuration._CONFIG_TEMPLATE_CREATED
    configuration._LANGUAGE_CACHE = None
    configuration._CONFIG_TEMPLATE_CREATED = False
    yield
    configuration._LANGUAGE_CACHE = original
    configuration._CONFIG_TEMPLATE_CREATED = original_template_flag


def _write_config(base_dir: Path, content: str) -> Path:
    config_dir = base_dir / "Config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "Config.ini"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def _assert_template_file_matches_defaults(template_path: Path) -> None:
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    parser.read(template_path, encoding="utf-8")

    for language in configuration.SUPPORTED_LANGUAGES:
        expected = configuration._materialise_template_defaults(language)
        for category, entries in expected.items():
            if language == configuration.DEFAULT_LANGUAGE:
                section_name = category
            else:
                section_name = f"{category}[{language}]"
            assert parser.has_section(section_name)
            for key, value in entries.items():
                assert parser.get(section_name, key) == value


def test_writeconfig_uses_placeholder_values(tmp_path):
    target_dir = tmp_path / "Config"
    configuration.writeconfig(str(target_dir))

    config_path = target_dir / "Config.ini"
    parser = configparser.RawConfigParser()
    parser.read(config_path)

    assert parser.get(configuration.TIMEZONE_SECTION, configuration.TIMEZONE_OPTION) == configuration.DEFAULT_TIMEZONE
    assert parser.get(configuration.LANGUAGE_SECTION, configuration.LANGUAGE_OPTION) == configuration.DEFAULT_LANGUAGE
    assert parser.getfloat(configuration.REQUEST_SECTION, configuration.REQUEST_TIMEOUT_KEY) == configuration.DEFAULT_REQUEST_TIMEOUT
    assert parser.getint("MonitorNum", "total") == 0

    mail_values = dict(parser.items(configuration.MAIL_SECTION))
    assert mail_values["smtp_server"] == "<SMTP_SERVER>"
    assert mail_values["smtp_port"] == "<SMTP_PORT>"
    assert mail_values["username"] == "<USERNAME>"
    assert mail_values["password"] == "<PASSWORD>"
    assert mail_values["from_addr"] == "<FROM_ADDRESS>"
    assert mail_values["to_addrs"] == "<TO_ADDRESSES>"
    assert "http" not in config_path.read_text(encoding="utf-8")
    assert "@" not in "".join(mail_values.values())

    template_path = target_dir / configuration.TEMPLATE_CONFIG_NAME
    assert template_path.exists()
    _assert_template_file_matches_defaults(template_path)


@pytest.mark.parametrize(
    "config_content",
    [
        "[Logging]\nlog_level=info\n",
        "[TimeZone]\n",  # 缺少 timezone 选项
    ],
)
def test_get_timezone_returns_default_when_section_or_option_missing(
    tmp_path, monkeypatch, caplog, config_content
):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    _write_config(tmp_path, config_content)

    caplog.set_level(logging.WARNING, logger=configuration.LOGGER.name)

    assert configuration.get_timezone() == configuration.DEFAULT_TIMEZONE
    assert configuration.DEFAULT_TIMEZONE == "0"
    assert "默认值" in caplog.text


def test_read_monitor_list_returns_structured_items(tmp_path, monkeypatch, caplog):
    base_dir = tmp_path / "apimonitor"
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(base_dir))
    config_content = """
[MonitorNum]
total = 2

[Monitor1]
name = API-A
url = http://example.com/api
type = get
interval = 30
email = ops@example.com
payload = {"token": "abc"}
headers = Accept=application/json

[Monitor2]
name = API-B
url =
type = UNKNOWN
interval = -1
"""
    caplog.set_level(logging.ERROR, logger=configuration.LOGGER.name)
    _write_config(base_dir, config_content)

    items = configuration.read_monitor_list()

    assert len(items) == 1
    item = items[0]
    assert item.name == "API-A"
    assert item.monitor_type == "GET"
    assert item.interval == 30
    assert item.payload == {"token": "abc"}
    assert item.headers == {"Accept": "application/json"}
    assert item.normalised_email() == "ops@example.com"
    assert "解析失败" in caplog.text


def test_read_monitor_list_returns_empty_when_total_missing(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    _write_config(tmp_path, "[Other]\nvalue=1\n")
    caplog.set_level(logging.ERROR, logger=configuration.LOGGER.name)

    items = configuration.read_monitor_list()

    assert items == []
    assert "MonitorNum.total" in caplog.text


def test_read_monitor_list_creates_template_when_missing(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_path = tmp_path / "Config" / "Config.ini"
    template_path = tmp_path / "Config" / configuration.TEMPLATE_CONFIG_NAME
    assert not config_path.exists()
    assert not template_path.exists()

    caplog.set_level(logging.INFO, logger=configuration.LOGGER.name)

    items = configuration.read_monitor_list()

    assert items == []
    assert config_path.exists()
    assert template_path.exists()

    relevant_records = [
        record for record in caplog.records if record.name == configuration.LOGGER.name
    ]
    assert relevant_records
    assert not any(record.levelno >= logging.ERROR for record in relevant_records)
    assert any("示例模板" in record.getMessage() for record in relevant_records)

    parser = configparser.RawConfigParser()
    parser.read(config_path)
    assert parser.getint("MonitorNum", "total") == 0

    _assert_template_file_matches_defaults(template_path)

    assert configuration.consume_config_template_created_flag() is True
    assert configuration.consume_config_template_created_flag() is False


def test_read_monitor_list_recovers_missing_template(tmp_path, monkeypatch, caplog):
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    template_path = config_dir / configuration.TEMPLATE_CONFIG_NAME
    template_path.unlink()

    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    caplog.set_level(logging.INFO, logger=configuration.LOGGER.name)

    configuration.get_template_manager().reload()
    items = configuration.read_monitor_list()

    assert items == []
    assert template_path.exists()
    assert configuration.consume_config_template_created_flag() is True

    relevant_records = [
        record for record in caplog.records if record.name == configuration.LOGGER.name
    ]
    assert any("模版文件缺失" in record.getMessage() for record in relevant_records)

    _assert_template_file_matches_defaults(template_path)


def test_write_config_parser_uses_utf8(tmp_path, monkeypatch):
    parser = configparser.RawConfigParser()
    parser.add_section("General")
    parser.set("General", "name", "接口监控")

    target = tmp_path / "Config.ini"
    original_open = Path.open
    observed: dict[str, object] = {}

    def strict_open(self, mode="r", *args, **kwargs):
        if self == target and "w" in mode:
            observed["encoding"] = kwargs.get("encoding")
            if kwargs.get("encoding") is None:
                raise UnicodeEncodeError("cp1252", b"", 0, 1, "encoding required")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", strict_open)

    configuration._write_config_parser(parser, target)

    assert observed.get("encoding") == "utf-8"
    assert "接口监控" in target.read_text(encoding="utf-8")


def test_render_template_refreshes_after_manual_update(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    template_path = config_dir / configuration.TEMPLATE_CONFIG_NAME

    configuration.get_template_manager().reload()
    original_value = configuration.render_template("log", "csv_header", {})

    parser = configparser.RawConfigParser()
    parser.optionxform = str
    parser.read(template_path, encoding="utf-8")
    updated_value = "Timestamp,Service,Type,url,Interval,Code,Status"
    parser.set("log", "csv_header", updated_value)
    with template_path.open("w", encoding="utf-8") as handle:
        parser.write(handle)

    configuration.get_template_manager().reload()
    configuration.read_monitor_list()
    refreshed_value = configuration.render_template("log", "csv_header", {})

    assert refreshed_value == updated_value
    assert refreshed_value != original_value


def test_get_preferences_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    prefs = configuration.get_preferences()

    assert prefs["theme"] is None
    assert prefs["theme_display_name"] is None
    assert prefs["theme_description"] is None
    assert prefs["theme_high_contrast"] is False
    assert prefs["language"] == configuration.DEFAULT_LANGUAGE
    assert prefs["timezone"] == configuration.DEFAULT_TIMEZONE


def test_set_preferences_updates_values(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    configuration.set_preferences(
        {
            "theme": "workspace_dark",
            "theme_display_name": "Workspace Dark",
            "theme_description": "Dark theme designed for low-light work",
            "theme_high_contrast": False,
            "language": "en_US",
            "timezone": -5,
        }
    )

    config_path = tmp_path / "Config" / "Config.ini"
    parser = configparser.RawConfigParser()
    parser.read(config_path)

    assert parser.get("Preferences", "theme") == "workspace_dark"
    assert (
        parser.get(configuration.LANGUAGE_SECTION, configuration.LANGUAGE_OPTION)
        == "en_US"
    )
    assert (
        parser.get(configuration.TIMEZONE_SECTION, configuration.TIMEZONE_OPTION)
        == "-5"
    )
    assert (
        parser.get(configuration.PREFERENCES_SECTION, configuration.THEME_DISPLAY_NAME_OPTION)
        == "Workspace Dark"
    )
    assert (
        parser.get(configuration.PREFERENCES_SECTION, configuration.THEME_DESCRIPTION_OPTION)
        == "Dark theme designed for low-light work"
    )
    assert (
        parser.get(configuration.PREFERENCES_SECTION, configuration.THEME_HIGH_CONTRAST_OPTION)
        == "false"
    )

    prefs = configuration.get_preferences()
    assert prefs["theme"] == "workspace_dark"
    assert prefs["theme_display_name"] == "Workspace Dark"
    assert prefs["theme_description"] == "Dark theme designed for low-light work"
    assert prefs["theme_high_contrast"] is False
    assert prefs["language"] == "en_US"
    assert prefs["timezone"] == "-5"


def test_set_preferences_supports_chinese_values(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    configuration.set_preferences(
        {
            "theme": "workspace_dark",
            "theme_display_name": "夜间主题",
            "theme_description": "适合夜间使用",
            "theme_high_contrast": False,
            "language": configuration.DEFAULT_LANGUAGE,
            "timezone": 8,
        }
    )

    config_path = tmp_path / "Config" / "Config.ini"
    text = config_path.read_text(encoding="utf-8")

    assert "夜间主题" in text
    assert "适合夜间使用" in text


def test_set_preferences_rejects_invalid_language(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    with pytest.raises(ValueError):
        configuration.set_preferences({"language": "fr_FR"})


def test_set_preferences_rejects_invalid_timezone(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    with pytest.raises(ValueError):
        configuration.set_preferences({"timezone": "invalid"})


def test_set_preferences_clears_theme(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    configuration.set_preferences(
        {
            "theme": "workspace_light",
            "theme_display_name": "Workspace Light",
            "theme_description": "Default light theme",
            "theme_high_contrast": False,
        }
    )
    configuration.set_preferences({"theme": ""})

    config_path = tmp_path / "Config" / "Config.ini"
    parser = configparser.RawConfigParser()
    parser.read(config_path)

    assert not parser.has_option(configuration.PREFERENCES_SECTION, configuration.THEME_OPTION)
    assert not parser.has_option(
        configuration.PREFERENCES_SECTION, configuration.THEME_DISPLAY_NAME_OPTION
    )
    assert not parser.has_option(
        configuration.PREFERENCES_SECTION, configuration.THEME_DESCRIPTION_OPTION
    )
    assert not parser.has_option(
        configuration.PREFERENCES_SECTION, configuration.THEME_HIGH_CONTRAST_OPTION
    )
    prefs = configuration.get_preferences()
    assert prefs["theme"] is None
    assert prefs["theme_display_name"] is None
    assert prefs["theme_description"] is None
    assert prefs["theme_high_contrast"] is False


def test_set_preferences_requires_mapping(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    with pytest.raises(TypeError):
        configuration.set_preferences(["theme", "workspace"])


def test_read_mail_configuration_falls_back_to_root_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(configuration.EXTERNAL_MAIL_CONFIG_ENV, raising=False)
    for env_name in configuration.MAIL_ENV_MAP.values():
        monkeypatch.delenv(env_name, raising=False)

    root_config = tmp_path / "config.ini"
    root_config.write_text(
        """
[Mail]
smtp_server = smtp.test.local
smtp_port = 587
username = notifier@test.local
password = secret
from_addr = notifier@test.local
to_addrs = ops@test.local
use_starttls = true
use_ssl = false
subject = Incident Alert
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path / "app_home"))

    mail_config = configuration.read_mail_configuration()

    assert mail_config["smtp_server"] == "smtp.test.local"
    assert mail_config["use_starttls"] is True
    assert mail_config["use_ssl"] is False


def test_write_monitor_list_supports_chinese_content(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    monitors = [
        {
            "name": "接口服务",
            "url": "https://example.com/api",
            "type": "GET",
            "interval": 30,
            "email": "报警@example.com",
            "payload": {"描述": "正常"},
            "headers": {"X-服务": "接口服务"},
            "language": configuration.DEFAULT_LANGUAGE,
        }
    ]

    configuration.write_monitor_list(monitors)

    config_path = tmp_path / "Config" / "Config.ini"
    text = config_path.read_text(encoding="utf-8")

    assert "接口服务" in text
    assert "报警@example.com" in text
    assert "描述" in text


def test_get_logging_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))

    settings = configuration.get_logging_settings()

    assert settings.level == logging.INFO
    assert settings.level_name == "INFO"
    assert settings.file_path == (tmp_path / "Log" / "system.log").resolve()
    assert settings.max_bytes == 10 * 1024 * 1024
    assert settings.backup_count == 5
    assert settings.console is True
    assert settings.fmt == "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    assert settings.datefmt == "%Y-%m-%d %H:%M:%S"


def test_configure_logging_installs_handlers(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    config_path = config_dir / "Config.ini"

    parser = configparser.RawConfigParser()
    parser.read(config_path, encoding="utf-8")
    parser.set("Logging", "log_level", "DEBUG")
    parser.set("Logging", "log_filename", "custom.log")
    parser.set("Logging", "log_max_size", "1MB")
    parser.set("Logging", "log_backup_count", "2")
    parser.set("Logging", "log_console", "false")
    parser.set("Logging", "log_format", "%(levelname)s::%(message)s")
    parser.set("Logging", "log_datefmt", "%H:%M:%S")
    with config_path.open("w", encoding="utf-8") as handle:
        parser.write(handle)

    configuration.reset_logging_configuration()
    settings = configuration.configure_logging(replace_existing=True)
    assert settings.level == logging.DEBUG
    assert settings.console is False
    assert settings.file_path == (tmp_path / "Log" / "custom.log").resolve()
    assert settings.max_bytes == 1 * 1024 * 1024
    assert settings.backup_count == 2
    assert settings.fmt == "%(levelname)s::%(message)s"
    assert settings.datefmt == "%H:%M:%S"

    root_logger = logging.getLogger()
    file_handlers = [
        handler for handler in root_logger.handlers if isinstance(handler, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    handler = file_handlers[0]
    assert handler.baseFilename == str(settings.file_path)
    assert handler.maxBytes == settings.max_bytes
    assert handler.backupCount == settings.backup_count
    assert handler.formatter._fmt == settings.fmt  # type: ignore[attr-defined]
    assert handler.formatter.datefmt == settings.datefmt  # type: ignore[attr-defined]

    matching_handlers = [
        handler
        for handler in root_logger.handlers
        if getattr(getattr(handler, "formatter", None), "_fmt", None) == settings.fmt
        and not isinstance(handler, RotatingFileHandler)
    ]
    assert matching_handlers == []

    configuration.reset_logging_configuration()


def test_get_logging_preferences_returns_user_values(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    config_path = config_dir / "Config.ini"

    parser = configparser.RawConfigParser()
    parser.read(config_path, encoding="utf-8")
    parser.set("Logging", "log_level", "WARNING")
    parser.set("Logging", "log_filename", "events.log")
    parser.set("Logging", "log_directory", str((tmp_path / "AltLogs").resolve()))
    parser.set("Logging", "log_max_size", "5MB")
    parser.set("Logging", "log_backup_count", "7")
    parser.set("Logging", "log_console", "false")
    parser.set("Logging", "log_format", "%(message)s")
    parser.set("Logging", "log_datefmt", "%H:%M")
    with config_path.open("w", encoding="utf-8") as handle:
        parser.write(handle)

    prefs = configuration.get_logging_preferences()

    assert prefs["level"] == "WARNING"
    assert prefs["filename"] == "events.log"
    assert Path(prefs["directory"]).resolve() == (tmp_path / "AltLogs").resolve()
    assert prefs["backup_count"] == 7
    assert prefs["console"] is False
    assert prefs["format"] == "%(message)s"
    assert prefs["datefmt"] == "%H:%M"
    assert pytest.approx(prefs["max_size_mb"], rel=1e-3) == 5.0


def test_set_logging_preferences_updates_config(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    config_path = config_dir / "Config.ini"

    custom_dir = (tmp_path / "alt_storage").resolve()

    settings = configuration.set_logging_preferences(
        level="ERROR",
        max_size="12.5MB",
        backup_count=3,
        console=False,
        directory=str(custom_dir),
        filename="alerts.log",
        fmt="%(levelname)s|%(message)s",
        datefmt="%H:%M:%S",
    )

    assert settings.level_name == "ERROR"
    assert settings.console is False
    assert settings.backup_count == 3
    assert settings.file_path == (custom_dir / "alerts.log").resolve()
    assert settings.fmt == "%(levelname)s|%(message)s"
    assert settings.datefmt == "%H:%M:%S"
    assert settings.max_bytes == pytest.approx(12.5 * 1024 * 1024, rel=1e-3)

    parser = configparser.RawConfigParser()
    parser.read(config_path, encoding="utf-8")
    assert parser.get("Logging", "log_level") == "ERROR"
    assert parser.get("Logging", "log_filename") == "alerts.log"
    assert Path(parser.get("Logging", "log_directory")).resolve() == custom_dir
    assert parser.get("Logging", "log_backup_count") == "3"
    assert parser.get("Logging", "log_console") == "false"
    assert parser.get("Logging", "log_format") == "%(levelname)s|%(message)s"
    assert parser.get("Logging", "log_datefmt") == "%H:%M:%S"
    settings = configuration.configure_logging(replace_existing=True)
    assert settings.level == logging.ERROR
    assert settings.console is False
    assert settings.file_path == (custom_dir / "alerts.log").resolve()
    assert settings.max_bytes == pytest.approx(12.5 * 1024 * 1024, rel=1e-3)
    assert settings.backup_count == 3
    assert settings.fmt == "%(levelname)s|%(message)s"
    assert settings.datefmt == "%H:%M:%S"

    root_logger = logging.getLogger()
    file_handlers = [
        handler for handler in root_logger.handlers if isinstance(handler, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    handler = file_handlers[0]
    assert handler.baseFilename == str(settings.file_path)
    assert handler.maxBytes == settings.max_bytes
    assert handler.backupCount == settings.backup_count
    assert handler.formatter._fmt == settings.fmt  # type: ignore[attr-defined]
    assert handler.formatter.datefmt == settings.datefmt  # type: ignore[attr-defined]

    matching_handlers = [
        handler
        for handler in root_logger.handlers
        if getattr(getattr(handler, "formatter", None), "_fmt", None) == settings.fmt
        and not isinstance(handler, RotatingFileHandler)
    ]
    assert matching_handlers == []

    configuration.reset_logging_configuration()
