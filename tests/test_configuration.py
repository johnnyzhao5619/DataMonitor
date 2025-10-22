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
