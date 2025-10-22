import logging
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration  # noqa: E402  pylint: disable=wrong-import-position


def _write_config(base_dir: Path, content: str) -> Path:
    config_dir = base_dir / "Config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "Config.ini"
    config_path.write_text(content, encoding="utf-8")
    return config_path


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
