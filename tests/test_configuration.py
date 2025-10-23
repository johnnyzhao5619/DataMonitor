import configparser
import logging
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
    configuration._LANGUAGE_CACHE = None
    yield
    configuration._LANGUAGE_CACHE = original


def _write_config(base_dir: Path, content: str) -> Path:
    config_dir = base_dir / "Config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "Config.ini"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def test_writeconfig_uses_placeholder_values(tmp_path):
    target_dir = tmp_path / "Config"
    configuration.writeconfig(str(target_dir))

    config_path = target_dir / "Config.ini"
    parser = configparser.RawConfigParser()
    parser.read(config_path)

    assert parser.get(configuration.TIMEZONE_SECTION, configuration.TIMEZONE_OPTION) == configuration.DEFAULT_TIMEZONE
    assert parser.get(configuration.LANGUAGE_SECTION, configuration.LANGUAGE_OPTION) == configuration.DEFAULT_LANGUAGE
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


def test_get_preferences_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    prefs = configuration.get_preferences()

    assert prefs["theme"] is None
    assert prefs["language"] == configuration.DEFAULT_LANGUAGE
    assert prefs["timezone"] == configuration.DEFAULT_TIMEZONE


def test_set_preferences_updates_values(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    configuration.set_preferences(
        {"theme": "workspace_dark", "language": "en_US", "timezone": -5}
    )

    config_path = tmp_path / "Config" / "Config.ini"
    parser = configparser.RawConfigParser()
    parser.read(config_path)

    assert parser.get("Preferences", "theme") == "workspace_dark"
    assert parser.get(configuration.LANGUAGE_SECTION, configuration.LANGUAGE_OPTION) == "en_US"
    assert parser.get(configuration.TIMEZONE_SECTION, configuration.TIMEZONE_OPTION) == "-5"

    prefs = configuration.get_preferences()
    assert prefs == {
        "theme": "workspace_dark",
        "language": "en_US",
        "timezone": "-5",
    }


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

    configuration.set_preferences({"theme": "workspace_light"})
    configuration.set_preferences({"theme": ""})

    config_path = tmp_path / "Config" / "Config.ini"
    parser = configparser.RawConfigParser()
    parser.read(config_path)

    assert not parser.has_option(configuration.PREFERENCES_SECTION, configuration.THEME_OPTION)
    prefs = configuration.get_preferences()
    assert prefs["theme"] is None


def test_set_preferences_requires_mapping(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    with pytest.raises(TypeError):
        configuration.set_preferences(["theme", "workspace"])
