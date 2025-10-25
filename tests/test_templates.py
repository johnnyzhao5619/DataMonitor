import logging
import sys
import types
from pathlib import Path

import pytest

if "requests" not in sys.modules:
    dummy_requests = types.ModuleType("requests")

    class _DummyRequestException(Exception):
        pass

    def _dummy_request(*args,
                       **kwargs):  # pragma: no cover - defensive debugging
        raise NotImplementedError(
            "requests module is unavailable in this test environment")

    dummy_requests.RequestException = _DummyRequestException
    dummy_requests.get = _dummy_request
    dummy_requests.post = _dummy_request
    sys.modules["requests"] = dummy_requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration  # noqa: E402  pylint: disable=wrong-import-position
from monitoring import send_email  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture(autouse=True)
def reset_template_manager():
    configuration.get_template_manager.cache_clear()
    yield
    configuration.get_template_manager.cache_clear()


def _prepare_config_dir(tmp_path: Path,
                        monkeypatch,
                        templates_content: str = None) -> Path:
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    monkeypatch.setattr(configuration, "_LANGUAGE_CACHE", None, raising=False)
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
        "status_label": " offline",
        "status_text": "Offline",
        "status_action": "Alert",
        "event_description": "Monitoring detected the service is unreachable",
        "time_label": "Occurred at",
        "event_timestamp": "2023-01-01 00:00:00",
    }
    context.update(overrides)
    return context


def test_render_template_uses_default_when_templates_missing(
        tmp_path, monkeypatch):
    _prepare_config_dir(tmp_path, monkeypatch)
    context = {
        "service_name": "DemoService",
        "status_label": " online",
        "event_timestamp": "2023-01-01 00:00:00",
    }

    rendered = configuration.render_template("ui", "status_line", context)
    assert rendered == "Time: 2023-01-01 00:00:00 --> Status: DemoService online"


def test_render_template_overrides_ini_file(tmp_path, monkeypatch):
    templates_content = """[ui]\nstatus_line = UI hint {service_name} -{status_label}\n"""
    _prepare_config_dir(tmp_path, monkeypatch, templates_content)

    context = {
        "service_name": "DemoService",
        "status_label": " offline",
        "event_timestamp": "2023-01-01 00:00:00",
    }

    rendered = configuration.render_template("ui", "status_line", context)
    assert rendered == "UI hint DemoService - offline"


def test_render_template_missing_variable(tmp_path, monkeypatch):
    _prepare_config_dir(tmp_path, monkeypatch)

    with pytest.raises(ValueError) as exc_info:
        configuration.render_template("mail", "alert_body",
                                      {"service_name": "Demo"})

    assert "missing variable" in str(exc_info.value)


def test_render_email_requires_fields(tmp_path, monkeypatch):
    _prepare_config_dir(tmp_path, monkeypatch)
    context = _sample_context()
    context.pop("time_label")

    with pytest.raises(ValueError) as exc_info:
        send_email.render_email("alert", context)

    assert "missing required fields" in str(exc_info.value)


def test_render_email_respects_template_override(tmp_path, monkeypatch):
    templates_content = """[mail]\nalert_subject = ALERT {service_name}\nalert_body = BODY {status_action}\n"""
    _prepare_config_dir(tmp_path, monkeypatch, templates_content)
    context = _sample_context()

    subject, body = send_email.render_email("alert", context)

    assert subject == "ALERT DemoService"
    assert body == "BODY Alert"


def test_render_email_supports_per_monitor_language(tmp_path, monkeypatch):
    templates_content = ("[mail]\n"
                         "alert_subject = DEFAULT {service_name}\n"
                         "alert_body = DEFAULT {time_label}\n"
                         "[mail[en_US]]\n"
                         "alert_subject = EN {service_name}\n"
                         "alert_body = EN {time_label}\n")
    _prepare_config_dir(tmp_path, monkeypatch, templates_content)
    configuration.get_template_manager().reload()

    default_context = _sample_context()
    subject_default, body_default = send_email.render_email(
        "alert", default_context)
    assert subject_default == "DEFAULT DemoService"
    assert body_default == "DEFAULT Occurred at"

    english_context = _sample_context(time_label="Occurred at")
    subject_en, body_en = send_email.render_email("alert",
                                                  english_context,
                                                  language="en_US")
    assert subject_en == "EN DemoService"
    assert body_en == "EN Occurred at"

    monkeypatch.setattr(configuration,
                        "_LANGUAGE_CACHE",
                        "en_US",
                        raising=False)
    configuration.get_template_manager().reload()
    subject_global, body_global = send_email.render_email(
        "alert", english_context)
    assert subject_global == "EN DemoService"
    assert body_global == "EN Occurred at"


def test_render_template_warns_when_ini_invalid(tmp_path, monkeypatch, caplog):
    templates_content = """[ui\nstatus_line = invalid config"""
    _prepare_config_dir(tmp_path, monkeypatch, templates_content)

    context = {
        "service_name": "DemoService",
        "status_label": " online",
        "event_timestamp": "2023-01-01 00:00:00",
    }

    logger_name = configuration.LOGGER.name
    with caplog.at_level(logging.WARNING, logger=logger_name):
        rendered = configuration.render_template("ui", "status_line", context)

    assert rendered == "Time: 2023-01-01 00:00:00 --> Status: DemoService online"
    relevant_records = [
        record for record in caplog.records if record.name == logger_name
    ]
    assert relevant_records
    assert any("Template config" in record.getMessage()
               for record in relevant_records)
