"""主题、语言与时区偏好控制器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PyQt5 import QtCore, QtWidgets

import configuration

from . import ControllerEventBus

_TranslatorBase = getattr(QtCore, "QTranslator", object)


class JsonTranslator(_TranslatorBase):
    """基于 JSON 存储的轻量级翻译器，实现 QTranslator 接口。"""

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        if _TranslatorBase is object:
            super().__init__()
        else:
            try:
                super().__init__(parent)
            except TypeError:
                super().__init__()
        self._catalog: dict[str, dict[str, str]] = {}
        self._language: Optional[str] = None

    def load(
        self,
        filename: str,
        directory: str = "",
        search_delimiters: str = "",
        suffix: str = "",
    ) -> bool:
        path = Path(filename)
        if directory:
            path = Path(directory) / path
        if suffix and not path.suffix:
            path = path.with_suffix(suffix)
        if not path.suffix:
            path = path.with_suffix(".qm")
        if not path.is_file():
            self._catalog = {}
            self._language = None
            return False

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            self._catalog = {}
            self._language = None
            return False

        messages = payload.get("messages")
        if not isinstance(messages, dict):
            self._catalog = {}
            self._language = None
            return False

        catalog: dict[str, dict[str, str]] = {}
        for context, entries in messages.items():
            if not isinstance(entries, dict):
                continue
            catalog[str(context)] = {
                str(source): str(target) for source, target in entries.items()
            }

        self._catalog = catalog
        self._language = (
            str(payload.get("language")) if payload.get("language") else None
        )
        return True

    def translate(
        self,
        context: str,
        source_text: str,
        disambiguation: Optional[str] = None,
        n: int = -1,
    ) -> str:
        if not source_text:
            return ""
        catalog = self._catalog.get(context) or {}
        translation = catalog.get(source_text)
        if translation is None:
            fallback = self._catalog.get("*") or {}
            translation = fallback.get(source_text)
        return translation if translation is not None else source_text

    @property
    def language(self) -> Optional[str]:
        return self._language


class PreferencesController(QtCore.QObject):
    """封装主题、语言和时区偏好逻辑。"""

    def __init__(
        self,
        *,
        window: QtWidgets.QWidget,
        ui,
        theme_manager,
        event_bus: ControllerEventBus,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.window = window
        self.ui = ui
        self.theme_manager = theme_manager
        self._event_bus = event_bus

        self._preferences = configuration.get_preferences()
        self._translator: Optional[JsonTranslator] = None
        self._current_language = configuration.get_language()
        self._time_zone = self._read_config_timezone()

    # --- 初始化 -----------------------------------------------------
    def setup(self) -> None:
        self._initialise_theme_selector()
        self._initialise_language_selector()
        self._update_timezone_display()
        self._event_bus.timezoneChanged.emit(self._time_zone)
        self._event_bus.languageChanged.emit(self._current_language)

    # --- 属性访问 ---------------------------------------------------
    @property
    def current_language(self) -> str:
        return self._current_language

    @property
    def current_timezone(self) -> int:
        return self._time_zone

    # --- 主题逻辑 ---------------------------------------------------
    def _initialise_theme_selector(self) -> None:
        selector = self.ui.themeSelector
        names = self.theme_manager.available_themes()
        selector.blockSignals(True)
        selector.clear()

        language = self._current_language or configuration.get_language()
        for name in names:
            theme = self.theme_manager.get_theme(name)
            display_text = self._display_theme_name(theme)
            description = theme.metadata.description_for(language)
            selector.addItem(display_text, name)
            index = selector.count() - 1
            selector.setItemData(index, description, QtCore.Qt.ToolTipRole)
            selector.setItemData(
                index, theme.metadata.is_high_contrast, QtCore.Qt.UserRole + 1
            )

        preferred_theme = None
        if isinstance(self._preferences, dict):
            preferred_theme = self._preferences.get("theme")

        current = self.theme_manager.current_theme_name()
        applied_theme = None

        if preferred_theme and preferred_theme not in names:
            for name in names:
                theme = self.theme_manager.get_theme(name)
                if theme.metadata.display_name == preferred_theme:
                    preferred_theme = name
                    break

        if preferred_theme and preferred_theme in names and preferred_theme != current:
            try:
                applied_theme = self.theme_manager.apply_theme(preferred_theme)
                current = preferred_theme
            except KeyError:
                configuration.LOGGER.warning(
                    "主题偏好 %s 未注册，使用当前主题", preferred_theme
                )

        if current is None and names:
            current = names[0]
            applied_theme = self.theme_manager.apply_theme(current)
        elif current and applied_theme is None:
            applied_theme = self.theme_manager.get_theme(current)

        if current:
            index = selector.findData(current)
            if index >= 0:
                selector.setCurrentIndex(index)

        selector.blockSignals(False)
        self._refresh_theme_widgets()

        if applied_theme is None and current:
            applied_theme = self.theme_manager.get_theme(current)
        if applied_theme is not None:
            self._persist_theme_preference(applied_theme)

    def on_theme_changed(self, index: int) -> None:
        name = self.ui.themeSelector.itemData(index)
        if not isinstance(name, str) or not name:
            return

        previous = self.theme_manager.current_theme_name()
        if previous != name:
            theme = self.theme_manager.apply_theme(name)
        else:
            theme = self.theme_manager.get_theme(name)

        self._refresh_theme_widgets()
        self._persist_theme_preference(theme, force=True)
        message = self.tr("已切换至主题: {name}").format(
            name=self._display_theme_name(theme)
        )
        self._event_bus.statusMessage.emit(message, 3000)
        self._event_bus.themeChanged.emit(theme.name)

    def _display_theme_name(self, theme) -> str:
        base_name = theme.metadata.display_name or theme.name
        translated = QtCore.QCoreApplication.translate("Theme", base_name)
        if theme.metadata.is_high_contrast:
            return self.tr("{name}（高对比）").format(name=translated)
        return translated

    def _refresh_theme_widgets(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            return

        for widget in (
            self.window,
            self.ui.central_widget,
            getattr(self.ui, "commandBar", None),
            self.ui.navigationBar,
            self.ui.contentStack,
            self.ui.monitorBrowser,
            self.ui.configWizard,
            getattr(self.ui, "preferencesPage", None),
            getattr(self.ui, "timezoneDisplay", None),
        ):
            if widget is None:
                continue
            app.style().unpolish(widget)
            app.style().polish(widget)
            widget.update()

    def _persist_theme_preference(self, theme, *, force: bool = False) -> None:
        metadata = theme.metadata
        display_name = metadata.display_name or theme.name
        language = self._current_language or configuration.get_language()
        description = metadata.description_for(language)
        payload = {
            "theme": theme.name,
            "theme_display_name": display_name,
            "theme_description": description,
            "theme_high_contrast": metadata.is_high_contrast,
        }

        preferences = getattr(self, "_preferences", None)
        if (
            not force
            and isinstance(preferences, dict)
            and preferences.get("theme") == payload["theme"]
            and preferences.get("theme_display_name") == payload["theme_display_name"]
            and preferences.get("theme_description") == payload["theme_description"]
            and preferences.get("theme_high_contrast") == payload["theme_high_contrast"]
        ):
            return

        configuration.set_preferences(payload)
        if isinstance(preferences, dict):
            preferences.update(payload)

    def update_theme_metadata(self) -> None:
        selector = self.ui.themeSelector
        language = self._current_language or configuration.get_language()
        for index in range(selector.count()):
            name = selector.itemData(index)
            if not isinstance(name, str) or not name:
                continue
            theme = self.theme_manager.get_theme(name)
            selector.setItemText(index, self._display_theme_name(theme))
            selector.setItemData(
                index,
                theme.metadata.description_for(language),
                QtCore.Qt.ToolTipRole,
            )
            selector.setItemData(
                index,
                theme.metadata.is_high_contrast,
                QtCore.Qt.UserRole + 1,
            )

    # --- 语言逻辑 ---------------------------------------------------
    def _initialise_language_selector(self) -> None:
        selector = self.ui.languageSelector
        languages = configuration.available_languages()
        selector.blockSignals(True)
        selector.clear()
        for code in languages:
            selector.addItem(self._describe_language(code), code)

        current = configuration.get_language()
        index = selector.findData(current)
        if index < 0 and selector.count():
            index = 0
        if index >= 0:
            selector.setCurrentIndex(index)
        selector.blockSignals(False)

        selected_code = selector.itemData(selector.currentIndex())
        if isinstance(selected_code, str) and selected_code:
            self._apply_language(selected_code, persist=False, notify=False)

    def on_language_changed(self, index: int) -> None:
        code = self.ui.languageSelector.itemData(index)
        if not isinstance(code, str) or not code:
            return
        if code == self._current_language:
            return
        self._apply_language(code)

    def _apply_language(
        self,
        code: str,
        *,
        persist: bool = True,
        notify: bool = True,
    ) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            return

        if self._translator is not None:
            app.removeTranslator(self._translator)
            self._translator = None

        translator = JsonTranslator()
        qm_path = self._translation_path(code)
        loaded = False
        if qm_path is not None and translator.load(str(qm_path)):
            app.installTranslator(translator)
            self._translator = translator
            loaded = True
        elif code == configuration.DEFAULT_LANGUAGE:
            loaded = True

        if not loaded:
            if code != configuration.DEFAULT_LANGUAGE:
                self._apply_language(
                    configuration.DEFAULT_LANGUAGE, persist=True, notify=notify
                )
            return

        previous_language = configuration.get_language()
        if persist:
            configuration.set_preferences({"language": code})
        elif code != previous_language:
            configuration.set_language(code)
        self._current_language = configuration.get_language()
        if isinstance(self._preferences, dict):
            self._preferences["language"] = self._current_language

        self.ui.retranslate_ui()
        self.ui.update_monitoring_controls(False)
        self.update_theme_metadata()
        self._refresh_theme_widgets()
        current_theme = self.theme_manager.current_theme()
        if current_theme is not None:
            self._persist_theme_preference(current_theme, force=True)
        self._update_timezone_display()
        configuration.get_template_manager().reload()

        self._event_bus.languageChanged.emit(self._current_language)

        if notify:
            message = self.tr("已切换至语言: {name}").format(
                name=self._describe_language(self._current_language)
            )
            self._event_bus.statusMessage.emit(message, 3000)

    def _describe_language(self, code: str) -> str:
        mapping = {
            "zh_CN": self.tr("简体中文"),
            "en_US": self.tr("English"),
        }
        return mapping.get(code, code)

    def _translation_path(self, code: str) -> Optional[Path]:
        base_dir = Path(__file__).resolve().parents[1] / "i18n"
        for filename in (f"{code}.qm.json", f"{code}.json", f"{code}.qm"):
            candidate = base_dir / filename
            if candidate.is_file():
                return candidate
        return None

    def refresh_language_items(self) -> None:
        selector = self.ui.languageSelector
        for index in range(selector.count()):
            code = selector.itemData(index)
            if isinstance(code, str) and code:
                selector.setItemText(index, self._describe_language(code))

    # --- 时区逻辑 ---------------------------------------------------
    def choose_timezone(self) -> None:
        time_zone, ok = QtWidgets.QInputDialog.getInt(
            self.window,
            self.tr("输入时区"),
            self.tr("请输入所在时区(整数):"),
            self._time_zone,
            -12,
            14,
            1,
        )
        if not ok:
            return

        self._time_zone = int(time_zone)
        configuration.set_preferences({"timezone": self._time_zone})
        if isinstance(self._preferences, dict):
            self._preferences["timezone"] = str(self._time_zone)
        self._update_timezone_display()
        self._event_bus.timezoneChanged.emit(self._time_zone)
        self._event_bus.statusMessage.emit(
            self.tr("已更新时区至 UTC{offset:+d}").format(offset=self._time_zone),
            3000,
        )

    def _read_config_timezone(self) -> int:
        raw_value = None
        if isinstance(self._preferences, dict):
            raw_value = self._preferences.get("timezone")
        if raw_value is None:
            raw_value = configuration.get_timezone()
        try:
            return int(str(raw_value).strip())
        except (TypeError, ValueError):
            return 0

    def _update_timezone_display(self) -> None:
        title = self.tr("本地时间 Local Time(时区 Time Zone: {zone})").format(
            zone=self._time_zone
        )
        self.ui.localTimeGroupBox.setTitle(title)
        if hasattr(self.ui, "set_timezone_hint"):
            self.ui.set_timezone_hint(self._time_zone)

    # --- 清理 -------------------------------------------------------
    def on_close(self) -> None:
        if self._translator is None:
            return
        app = QtWidgets.QApplication.instance()
        if app is None:
            return
        app.removeTranslator(self._translator)
        self._translator = None


__all__ = ["PreferencesController", "JsonTranslator"]
