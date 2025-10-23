import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "i18n" / "catalog.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture(autouse=True)
def reset_template_manager():
    configuration.get_template_manager.cache_clear()
    yield
    configuration.get_template_manager.cache_clear()


def _load_catalog():
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    contexts = {}
    for context in payload.get("contexts", []):
        name = context["name"]
        mapping = {}
        for message in context.get("messages", []):
            mapping[message["source"]] = message["translations"]
        contexts[name] = mapping
    return tuple(payload.get("languages", [])), contexts


def test_translation_files_match_catalog():
    languages, contexts = _load_catalog()
    assert languages, "catalog.json 必须定义语言列表"

    for language in languages:
        path = PROJECT_ROOT / "i18n" / f"{language}.qm.json"
        assert path.is_file(), f"缺少翻译文件: {path.name}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload.get("language") == language
        messages = payload.get("messages", {})
        assert set(messages) == set(contexts), "上下文集合不一致"
        for context_name, source_map in contexts.items():
            translations = messages[context_name]
            assert set(translations) == set(source_map), f"{context_name} 键集合不一致"
            for source, per_language in source_map.items():
                value = translations[source]
                expected = per_language[language]
                assert value == expected
                assert value, f"{context_name}:{source} 在 {language} 中为空"


def test_mail_templates_render_in_each_language(tmp_path, monkeypatch):
    languages, contexts = _load_catalog()
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    base_context = {
        "service_name": "DemoService",
        "event_timestamp": "2023-01-01 00:00:00",
    }
    per_language_context = {
        "zh_CN": {
            "status_action": "告警",
            "event_description": "监控检测到服务不可达",
            "time_label": "发生时间",
        },
        "en_US": {
            "status_action": "Alert",
            "event_description": "Service unreachable",
            "time_label": "Occurred at",
        },
    }

    catalog_map = contexts
    mail_resources = configuration.TEMPLATE_DEFAULTS["mail"]

    for language in languages:
        config_context = {**base_context, **per_language_context.get(language, {})}
        monkeypatch.setattr(configuration, "_LANGUAGE_CACHE", language, raising=False)
        configuration.get_template_manager().reload()
        subject_resource = mail_resources["alert_subject"]
        expected_subject_template = catalog_map[subject_resource.context][
            subject_resource.source
        ][language]
        rendered_subject = configuration.render_template(
            "mail", "alert_subject", config_context, language=language
        )
        assert rendered_subject == expected_subject_template.format(**config_context)

        body_resource = mail_resources["alert_body"]
        expected_body_template = catalog_map[body_resource.context][body_resource.source][
            language
        ]
        rendered_body = configuration.render_template(
            "mail", "alert_body", config_context, language=language
        )
        assert rendered_body == expected_body_template.format(**config_context)


def test_main_window_report_placeholder_translated():
    languages, contexts = _load_catalog()
    source = "Reports and alerts view under construction. Stay tuned!"

    assert "MainWindowUI" in contexts, "缺少 MainWindowUI 上下文"
    translations = contexts["MainWindowUI"].get(source)
    assert translations is not None, "缺少报表占位文案"

    expected = {
        "en_US": source,
        "zh_CN": "报表与告警视图建设中，敬请期待",
    }
    for language in languages:
        assert language in translations, f"{language} 缺少报表占位翻译"
        assert translations[language] == expected.get(language, translations[language])
        assert translations[language], f"{language} 的报表占位翻译为空"
