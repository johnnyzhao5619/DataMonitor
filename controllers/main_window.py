"""主窗口控制器模块，负责协调 UI 与监控调度。"""

from __future__ import annotations

import datetime
import json
import queue
import threading
from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox

import apiMonitor
import configuration
from configuration import SUPPORTED_MONITOR_TYPES
import logRecorder
from monitoring.service import (
    MonitorScheduler,
    parse_network_address as service_parse_network_address,
)
from monitoring.state_machine import MonitorEvent
from ui.main_window import MainWindowUI

if TYPE_CHECKING:
    from ui.theme import ThemeManager


PeriodicMonitorKey = Tuple[str, str, str]

_QObjectBase = getattr(QtCore, "QObject", object)
_StatusBarClass = getattr(QtWidgets, "QStatusBar", None)
_TranslatorBase = getattr(QtCore, "QTranslator", object)


class JsonTranslator(_TranslatorBase):
    """基于 JSON 存储的轻量级翻译器，实现 QTranslator 接口。"""

    def __init__(self, parent=None):
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
        self._language = str(payload.get("language")) if payload.get("language") else None
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


class _SilentStatusBar:
    def showMessage(self, *_args, **_kwargs):
        return None


class MainWindowController(_QObjectBase):
    """协调主窗口 UI 与业务逻辑的核心控制器。"""

    def __init__(
        self,
        window: QtWidgets.QMainWindow,
        ui: MainWindowUI,
        theme_manager: "ThemeManager",
    ) -> None:
        super().__init__(window)
        self.window = window
        self.ui = ui
        self.theme_manager = theme_manager

        status_bar = None
        status_accessor = getattr(self.window, "statusBar", None)
        if callable(status_accessor):
            try:
                status_bar = status_accessor()
            except Exception:
                status_bar = None

        if status_bar is None and _StatusBarClass is not None and hasattr(self.window, "setStatusBar"):
            try:
                status_bar = _StatusBarClass(self.window)
                self.window.setStatusBar(status_bar)
            except Exception:
                status_bar = None

        if status_bar is None:
            status_bar = _SilentStatusBar()

        self.status = status_bar
        if hasattr(self.status, "showMessage"):
            self.status.showMessage(self.tr('>>初始化...'), 4000)

        if hasattr(self.window, "setWindowTitle"):
            self.window.setWindowTitle(self.tr('Monitor Everything v0.2'))

        self.switch_status = True
        self.printf_queue: queue.Queue = queue.Queue()
        self._preferences = configuration.get_preferences()
        self.time_zone = self._read_config_timezone()
        self.scheduler: Optional[MonitorScheduler] = None
        self._periodic_scheduler = MonitorScheduler(
            event_handler=self._handle_monitor_event,
            timezone_getter=lambda: self.time_zone,
        )
        self._periodic_monitors: dict[PeriodicMonitorKey, configuration.MonitorItem] = {}
        self._periodic_timers: dict[PeriodicMonitorKey, QtCore.QTimer] = {}
        self._running_periodic: set[PeriodicMonitorKey] = set()

        self._clock_timer = QtCore.QTimer(self.window)
        self._clock_timer.timeout.connect(self.update_clock)
        self._clock_timer.start(1000)

        self.ui.switchButton.clicked.connect(self.start_monitor)
        self.ui.configButton.clicked.connect(self.show_configuration)
        self.ui.locationButton.clicked.connect(self.set_location)
        self.ui.configWizard.monitorsSaved.connect(self._handle_monitors_saved)
        self.ui.configWizard.requestReload.connect(self._reload_monitors)

        self._translator: Optional[JsonTranslator] = None
        self._current_language = configuration.get_language()

        self._initialise_theme_selector()
        self._initialise_language_selector()

        self._reload_monitors()
        self._update_timezone_display()
        self.update_clock()

    # --- 主题与外观 -----------------------------------------------------
    def _initialise_theme_selector(self) -> None:
        selector = self.ui.themeSelector
        names = self.theme_manager.available_themes()
        selector.blockSignals(True)
        selector.clear()
        selector.addItems(names)

        preferred_theme = None
        if hasattr(self, "_preferences"):
            preferred_theme = self._preferences.get("theme")

        current = self.theme_manager.current_theme_name()
        if preferred_theme and preferred_theme in names and preferred_theme != current:
            try:
                self.theme_manager.apply_theme(preferred_theme)
                current = preferred_theme
            except KeyError:
                configuration.LOGGER.warning(
                    "主题偏好 %s 未注册，使用当前主题", preferred_theme
                )

        if current is None and names:
            current = names[0]
            self.theme_manager.apply_theme(current)

        if current:
            index = selector.findText(current)
            if index >= 0:
                selector.setCurrentIndex(index)

        selector.blockSignals(False)
        selector.currentTextChanged.connect(self._on_theme_changed)
        self._refresh_theme_widgets()

        if hasattr(self, "_preferences"):
            self._preferences["theme"] = current

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
        selector.currentIndexChanged.connect(self._on_language_changed)

        selected_code = selector.itemData(selector.currentIndex())
        if isinstance(selected_code, str) and selected_code:
            self._apply_language(selected_code, persist=False, notify=False)

    def _on_theme_changed(self, name: str) -> None:
        if not name:
            return

        previous = self.theme_manager.current_theme_name()
        if previous != name:
            self.theme_manager.apply_theme(name)

        self._refresh_theme_widgets()
        configuration.set_preferences({"theme": name})
        if hasattr(self, "_preferences"):
            self._preferences["theme"] = name
        self.status.showMessage(
            self.tr('已切换至主题: {name}').format(name=name), 3000
        )

    def _on_language_changed(self, index: int) -> None:
        code = self.ui.languageSelector.itemData(index)
        if not isinstance(code, str) or not code:
            return
        if code == self._current_language:
            return
        self._apply_language(code)

    def _describe_language(self, code: str) -> str:
        mapping = {
            "zh_CN": self.tr("简体中文"),
            "en_US": self.tr("English"),
        }
        return mapping.get(code, code)

    def _translation_path(self, code: str) -> Optional[Path]:
        base_dir = Path(__file__).resolve().parents[1] / "i18n"
        candidate = base_dir / f"{code}.qm"
        if candidate.is_file():
            return candidate
        return None

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
        if hasattr(self, "_preferences"):
            self._preferences["language"] = self._current_language

        self.ui.retranslate_ui()
        self._refresh_language_items()
        if not self.switch_status:
            self.ui.switchButton.setText(self.tr('关闭 Close'))
        self._refresh_theme_widgets()
        self._update_timezone_display()

        if notify:
            self.status.showMessage(
                self.tr('已切换至语言: {name}').format(
                    name=self._describe_language(self._current_language)
                ),
                3000,
            )

    def _refresh_language_items(self) -> None:
        selector = self.ui.languageSelector
        for index in range(selector.count()):
            code = selector.itemData(index)
            if isinstance(code, str) and code:
                selector.setItemText(index, self._describe_language(code))

    def _refresh_theme_widgets(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            return

        for widget in (
            self.window,
            self.ui.central_widget,
            self.ui.navigationBar,
            self.ui.contentStack,
            self.ui.monitorBrowser,
            self.ui.configWizard,
        ):
            if widget is None:
                continue
            app.style().unpolish(widget)
            app.style().polish(widget)
            widget.update()

    # --- 监控调度 -------------------------------------------------------
    def start_monitor(self) -> None:
        if self.switch_status is True:
            monitor_list = configuration.read_monitor_list()
            self.printf_queue.put(
                self.tr("目前读取到{count}个监控项，分别是：").format(
                    count=len(monitor_list)
                )
            )
            for index, monitor in enumerate(monitor_list, start=1):
                self.printf_queue.put(
                    self.tr(
                        "{index}. {name} --- 类型: {monitor_type} --- 地址: {url} --- 周期: {interval}秒"
                    ).format(
                        index=index,
                        name=monitor.name,
                        monitor_type=monitor.monitor_type,
                        url=monitor.url,
                        interval=monitor.interval,
                    )
                )

            if not monitor_list:
                self.status.showMessage(self.tr('未读取到有效的监控配置'))
                return

            self.scheduler = MonitorScheduler(
                event_handler=self._handle_monitor_event,
                timezone_getter=lambda: self.time_zone,
            )
            self.scheduler.start(monitor_list)

            self.ui.show_monitor_page()
            self.ui.switchButton.setText(self.tr('关闭 Close'))
            self.switch_status = False
        else:
            if self.scheduler:
                self.scheduler.stop()
            QtWidgets.QApplication.quit()

    def perform_task(self, url, parsed_address, monitor_type, email, payload=None, *, headers=None):
        monitor_type_normalised = str(monitor_type).strip().upper() if monitor_type else ""
        if monitor_type_normalised == "GET":
            return apiMonitor.monitor_get(url)
        if monitor_type_normalised == "POST":
            return apiMonitor.monitor_post(url, payload, headers=headers)
        if monitor_type_normalised == "SERVER":
            address = parsed_address or service_parse_network_address(url)
            return apiMonitor.monitor_server(address)

        self._log_unsupported_type(monitor_type, url)
        return False

    def _handle_monitor_event(self, event: MonitorEvent) -> None:
        self.printf_queue.put(event.message)
        if event.status_bar_message:
            self.status.showMessage(event.status_bar_message)

    def parse_network_address(self, address):
        """解析网络地址字符串。"""

        return service_parse_network_address(address)

    def run_periodically(self, monitorInfo):
        monitor = self._build_monitor_item(monitorInfo)
        if monitor is None:
            return

        key = self._make_periodic_key(monitor)
        self._periodic_monitors[key] = monitor
        self._trigger_periodic_monitor(key)
        self._schedule_periodic_monitor(monitor, key)

    # --- 配置与表单 -----------------------------------------------------
    def show_configuration(self) -> None:
        self._reload_monitors()
        self.ui.show_configuration_page()
        self.status.showMessage(self.tr('>>配置模式'), 3000)

    def set_location(self) -> None:
        time_zone, ok = QInputDialog.getInt(
            self.window,
            self.tr("输入时区"),
            self.tr("请输入所在时区(整数):"),
            self.time_zone,
            -12,
            14,
            1,
        )
        if ok:
            self.time_zone = time_zone
            configuration.set_preferences({"timezone": time_zone})
            if hasattr(self, "_preferences"):
                self._preferences["timezone"] = str(time_zone)
            self._update_timezone_display()
            self.update_clock()

    def _handle_monitors_saved(self, monitors):
        try:
            configuration.write_monitor_list(monitors)
        except Exception as exc:
            QMessageBox.critical(
                self.window, self.tr('保存失败'), str(exc)
            )
            self.status.showMessage(
                self.tr('保存失败: {error}').format(error=exc), 5000
            )
        else:
            self.status.showMessage(self.tr('配置已保存'), 4000)
            self._reload_monitors()
            self.ui.show_monitor_page()

    def _reload_monitors(self):
        monitors = configuration.read_monitor_list()
        self.ui.configWizard.load_monitors(monitors)

    def _build_monitor_item(self, monitorInfo):
        if isinstance(monitorInfo, configuration.MonitorItem):
            return monitorInfo

        name = monitorInfo.get("name")
        url = monitorInfo.get("url")
        if not name or not url:
            self.printf_queue.put(self.tr("监控项配置缺少名称或地址"))
            return None

        raw_type = monitorInfo.get("type")
        monitor_type = ""
        if isinstance(raw_type, str):
            monitor_type = raw_type.strip().upper()
        elif raw_type is None:
            monitor_type = ""
        else:
            self._log_unsupported_type(raw_type, url, name=name)
            return None

        if monitor_type not in SUPPORTED_MONITOR_TYPES:
            self._log_unsupported_type(monitor_type or raw_type, url, name=name)
            return None

        try:
            interval = int(monitorInfo.get("interval", 0))
        except (TypeError, ValueError):
            self.printf_queue.put(
                self.tr("监控项[{name}]的周期配置无效: {value}").format(
                    name=name, value=monitorInfo.get('interval')
                )
            )
            return None

        return configuration.MonitorItem(
            name=name,
            url=url,
            monitor_type=monitor_type,
            interval=interval,
            email=monitorInfo.get("email"),
            payload=monitorInfo.get("payload"),
            headers=monitorInfo.get("headers"),
        )

    def _log_unsupported_type(self, monitor_type, url, name=None):
        monitor_name = f"[{name}]" if name else ""
        readable_type = monitor_type if monitor_type not in (None, "") else "<empty>"
        message = self.tr("监控项{monitor_name}类型 '{monitor_type}' 未被支持，URL: {url}").format(
            monitor_name=monitor_name,
            monitor_type=readable_type,
            url=url,
        )
        logRecorder.record("Unsupported Monitor Type", message)
        self.printf_queue.put(message)
        try:
            self.status.showMessage(message)
        except Exception:
            pass
        return message

    def _read_config_timezone(self):
        raw_value = None
        if hasattr(self, "_preferences"):
            raw_value = self._preferences.get("timezone")
        if raw_value is None:
            raw_value = configuration.get_timezone()
        try:
            return int(str(raw_value).strip())
        except (TypeError, ValueError):
            return 0

    def _update_timezone_display(self):
        title = self.tr('本地时间 Local Time(时区 Time Zone: {zone})').format(
            zone=self.time_zone
        )
        self.ui.localTimeGroupBox.setTitle(title)

    # --- 时钟与日志 -----------------------------------------------------
    def update_clock(self) -> None:
        utc_time = datetime.datetime.utcnow()
        current_time = utc_time + datetime.timedelta(hours=self.time_zone)
        self.ui.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.ui.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))

        while True:
            try:
                message = self.printf_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.ui.monitorBrowser.append(message)
                cursor = self.ui.monitorBrowser.textCursor()
                self.ui.monitorBrowser.moveCursor(cursor.End)
                QtWidgets.QApplication.processEvents()

    # --- 周期性监控 -----------------------------------------------------
    def _make_periodic_key(self, monitor: configuration.MonitorItem) -> PeriodicMonitorKey:
        return (monitor.name, monitor.url, monitor.monitor_type)

    def _trigger_periodic_monitor(self, monitor_key: PeriodicMonitorKey):
        monitor = self._periodic_monitors.get(monitor_key)
        if not monitor:
            timer = self._periodic_timers.pop(monitor_key, None)
            if timer:
                timer.stop()
            return

        if monitor_key in self._running_periodic:
            return

        self._running_periodic.add(monitor_key)

        def _run_cycle():
            try:
                self._periodic_scheduler.run_single_cycle(monitor)
            finally:
                self._running_periodic.discard(monitor_key)

        thread = threading.Thread(
            name=f"Monitor:{monitor.name}",
            target=_run_cycle,
            daemon=True,
        )
        thread.start()

    def _schedule_periodic_monitor(
        self,
        monitor: configuration.MonitorItem,
        monitor_key: PeriodicMonitorKey,
    ):
        interval_ms = max(int(monitor.interval), 0) * 1000
        timer = self._periodic_timers.get(monitor_key)

        if interval_ms == 0:
            if timer:
                timer.stop()
            return

        if timer is None:
            timer = QtCore.QTimer(self.window)
            timer.setSingleShot(False)
            timer.timeout.connect(
                lambda key=monitor_key: self._trigger_periodic_monitor(key)
            )
            self._periodic_timers[monitor_key] = timer

        timer.setInterval(interval_ms)
        if not timer.isActive():
            timer.start()

    def _stop_periodic_monitors(self):
        for timer in self._periodic_timers.values():
            timer.stop()
        self._periodic_timers.clear()
        self._periodic_monitors.clear()
        self._running_periodic.clear()
        self._periodic_scheduler.stop()
        self._periodic_scheduler = MonitorScheduler(
            event_handler=self._handle_monitor_event,
            timezone_getter=lambda: self.time_zone,
        )

    def on_close(self) -> None:
        if self.scheduler:
            self.scheduler.stop()
        self._stop_periodic_monitors()


__all__ = ["MainWindowController"]
