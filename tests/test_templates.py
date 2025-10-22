import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration  # noqa: E402  pylint: disable=wrong-import-position
import sendEmail  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture(autouse=True)
def reset_template_manager():
    configuration.get_template_manager.cache_clear()
    yield
    configuration.get_template_manager.cache_clear()


def _prepare_config_dir(tmp_path: Path, monkeypatch, templates_content: str = None) -> Path:
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_dir = tmp_path / "Config"
    config_dir.mkdir(parents=True, exist_ok=True)
    if templates_content is not None:
        template_path = config_dir / configuration.TEMPLATE_CONFIG_NAME
        template_path.write_text(templates_content, encoding="utf-8")
    return config_dir


def _sample_context(**overrides):
    context = {
        "service_name": "DemoService",
        "monitor_type": "GET",
        "url": "https://example.com",
        "interval": 60,
        "status_code": 3,
        "status_key": "alert",
        "status_label": "服务异常",
        "status_text": "异常",
        "status_action": "告警",
        "event_description": "监控检测到服务不可达",
        "time_label": "发生时间",
        "event_timestamp": "2023-01-01 00:00:00",
    }
    context.update(overrides)
    return context


def test_render_template_uses_default_when_templates_missing(tmp_path, monkeypatch):
    _prepare_config_dir(tmp_path, monkeypatch)
    context = {
        "service_name": "DemoService",
        "status_label": "服务正常",
        "event_timestamp": "2023-01-01 00:00:00",
    }

    rendered = configuration.render_template("ui", "status_line", context)
    assert rendered == "时间：2023-01-01 00:00:00 --> 状态：DemoService服务正常"


def test_render_template_overrides_ini_file(tmp_path, monkeypatch):
    templates_content = """[ui]\nstatus_line = UI提示 {service_name} - {status_label}\n"""
    _prepare_config_dir(tmp_path, monkeypatch, templates_content)

    context = {
        "service_name": "DemoService",
        "status_label": "服务异常",
        "event_timestamp": "2023-01-01 00:00:00",
    }

    rendered = configuration.render_template("ui", "status_line", context)
    assert rendered == "UI提示 DemoService - 服务异常"


def test_render_template_missing_variable(tmp_path, monkeypatch):
    _prepare_config_dir(tmp_path, monkeypatch)

    with pytest.raises(ValueError) as exc_info:
        configuration.render_template("mail", "alert_body", {"service_name": "Demo"})

    assert "缺少变量" in str(exc_info.value)


def test_render_email_requires_fields(tmp_path, monkeypatch):
    _prepare_config_dir(tmp_path, monkeypatch)
    context = _sample_context()
    context.pop("time_label")

    with pytest.raises(ValueError) as exc_info:
        sendEmail.render_email("alert", context)

    assert "缺少必要字段" in str(exc_info.value)


def test_render_email_respects_template_override(tmp_path, monkeypatch):
    templates_content = """[mail]\nalert_subject = ALERT {service_name}\nalert_body = BODY {status_action}\n"""
    _prepare_config_dir(tmp_path, monkeypatch, templates_content)
    context = _sample_context()

    subject, body = sendEmail.render_email("alert", context)

    assert subject == "ALERT DemoService"
    assert body == "BODY 告警"
