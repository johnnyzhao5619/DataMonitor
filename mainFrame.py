from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox

from ui.main_window import MainWindowUI
import apiMonitor
import configuration
from configuration import SUPPORTED_MONITOR_TYPES
import datetime
import shutil
import subprocess
import logRecorder
import sys
import queue
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.theme import ThemeManager

from monitoring.service import (
    MonitorScheduler,
    parse_network_address as service_parse_network_address,
)
from monitoring.state_machine import MonitorEvent
from i18n import FALLBACK_TRANSLATIONS

_QtTranslatorBase = getattr(QtCore, "QTranslator", object)


_QObjectBase = getattr(QtCore, "QObject", object)


class DictionaryTranslator(_QtTranslatorBase):
    def __init__(self, mapping: Dict[str, Dict[str, str]], parent=None):
        init = getattr(super(), "__init__", None)
        if callable(init):
            init(parent)
        self._mapping = mapping

    def translate(self, context, source_text, disambiguation=None, n=-1):
        context_map = self._mapping.get(context)
        if not context_map:
            return source_text
        return context_map.get(source_text, source_text)


class _SilentStatusBar:
    def showMessage(self, *_args, **_kwargs):
        return None


PeriodicMonitorKey = Tuple[str, str, str]


class MainWindowController(_QObjectBase):
    """协调主窗口 UI 与业务逻辑的控制器。"""

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

        self.status = self.window.statusBar()
        self._translator: Optional[QtCore.QTranslator] = None
        self._language_items: Tuple[Tuple[str, str], ...] = ()

        self.switch_status = True
        self.printf_queue: queue.Queue = queue.Queue()
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

        self._initialise_theme_selector()
        self._initialise_language_selector()

        self._reload_monitors()
        self._update_timezone_display()
        self.update_clock()
        self.status.showMessage(self._translate('>>初始化...'), 4000)

    def _translate(self, text: str) -> str:
        tr_method = getattr(self, "tr", None)
        if callable(tr_method):
            return tr_method(text)
        app_class = getattr(QtCore, "QCoreApplication", None)
        translate = getattr(app_class, "translate", None) if app_class else None
        if callable(translate):
            return translate("MainWindowController", text)
        return text

    def start_monitor(self) -> None:
        if self.switch_status is True:
            monitor_list = configuration.read_monitor_list()
            self.printf_queue.put(
                self._translate("目前读取到{count}个监控项，分别是：").format(
                    count=len(monitor_list)
                )
            )
            for index, monitor in enumerate(monitor_list, start=1):
                self.printf_queue.put(
                    self._translate(
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
                self.status.showMessage(self._translate('未读取到有效的监控配置'))
                return

            self.scheduler = MonitorScheduler(
                event_handler=self._handle_monitor_event,
                timezone_getter=lambda: self.time_zone,
            )
            self.scheduler.start(monitor_list)

            self.ui.show_monitor_page()
            self.ui.switchButton.setText(self._translate('关闭'))
            self.switch_status = False
        else:
            if self.scheduler:
                self.scheduler.stop()
            QtWidgets.QApplication.quit()

    def show_configuration(self) -> None:
        self._reload_monitors()
        self.ui.show_configuration_page()
        self.status.showMessage(self._translate('>>配置模式'), 3000)

    def set_location(self) -> None:
        time_zone, ok = QInputDialog.getInt(
            self.window,
            self._translate("输入时区"),
            self._translate("请输入所在时区(整数):"),
            self.time_zone,
            -12,
            14,
            1,
        )
        if ok:
            self.time_zone = time_zone
            configuration.set_timezone(str(time_zone))
            self._update_timezone_display()
            self.update_clock()

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

    def _initialise_theme_selector(self) -> None:
        selector = self.ui.themeSelector
        names = self.theme_manager.available_themes()
        selector.blockSignals(True)
        selector.clear()
        selector.addItems(names)

        current = self.theme_manager.current_theme_name()
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

    def _initialise_language_selector(self) -> None:
        selector = self.ui.languageSelector
        self._language_items = configuration.available_languages()
        selector.blockSignals(True)
        selector.clear()
        for code, label in self._language_items:
            selector.addItem("", (code, label))
        selector.blockSignals(False)
        selector.currentIndexChanged.connect(self._on_language_changed)
        self._apply_language(configuration.get_language(), announce=False)

    def _translation_path(self, language: str) -> Path:
        base_dir = Path(__file__).resolve().parent / "i18n"
        return base_dir / f"{language}.qm"

    def _ensure_translation_compiled(self, language: str) -> None:
        qm_path = self._translation_path(language)
        if qm_path.is_file():
            return
        ts_path = qm_path.with_suffix(".ts")
        if not ts_path.is_file():
            return
        compiler = shutil.which("lrelease") or shutil.which("lrelease-qt5")
        if not compiler:
            return
        try:
            subprocess.run([compiler, str(ts_path)], check=True, cwd=str(ts_path.parent))
        except Exception:
            return

    def _language_display_name(self, language: str) -> str:
        for code, label in self._language_items:
            if code == language:
                return self._translate(label) if isinstance(label, str) else str(label)
        return language

    def _sync_language_selector(self, language: str) -> None:
        selector = self.ui.languageSelector
        selector.blockSignals(True)
        try:
            for index in range(selector.count()):
                data = selector.itemData(index, QtCore.Qt.UserRole)
                if data and data[0] == language:
                    selector.setCurrentIndex(index)
                    break
        finally:
            selector.blockSignals(False)

    def _apply_language(
        self, language: str, *, announce: bool, update_selector: bool = True
    ) -> None:
        configuration.set_language(language)
        language_code = configuration.get_language()
        self._ensure_translation_compiled(language_code)
        translator_class = getattr(QtCore, "QTranslator", None)
        app = QtWidgets.QApplication.instance()
        if app is not None:
            if self._translator is not None:
                app.removeTranslator(self._translator)
            translator = None
            loaded = False
            if translator_class is not None:
                translator = translator_class(self.window)
                qm_path = self._translation_path(language_code)
                if qm_path.is_file() and translator.load(str(qm_path)):
                    app.installTranslator(translator)
                    self._translator = translator
                    loaded = True
            if not loaded:
                fallback_map = FALLBACK_TRANSLATIONS.get(language_code)
                if app is not None and fallback_map:
                    fallback_translator = DictionaryTranslator(
                        fallback_map, self.window
                    )
                    app.installTranslator(fallback_translator)
                    self._translator = fallback_translator
                    loaded = True
            if not loaded:
                self._translator = None

        self.ui.retranslate_ui()
        self._update_timezone_display()
        self._retranslate_controller_ui()
        if update_selector:
            self._sync_language_selector(language_code)
        if announce:
            language_name = self._language_display_name(language_code)
            self.status.showMessage(
                self._translate("已切换至语言：{name}").format(name=language_name), 3000
            )

    def _retranslate_controller_ui(self) -> None:
        self.window.setWindowTitle(self._translate("Monitor Everything v0.2"))
        if self.switch_status:
            self.ui.switchButton.setText(self._translate("监控"))
        else:
            self.ui.switchButton.setText(self._translate("关闭"))

    def _on_language_changed(self, index: int) -> None:
        data = self.ui.languageSelector.itemData(index, QtCore.Qt.UserRole)
        if not data:
            return
        code, _label = data
        self._apply_language(code, announce=True, update_selector=False)

    def _on_theme_changed(self, name: str) -> None:
        if not name:
            return

        previous = self.theme_manager.current_theme_name()
        if previous != name:
            self.theme_manager.apply_theme(name)

        self._refresh_theme_widgets()
        self.status.showMessage(
            self._translate('已切换至主题：{name}').format(name=name), 3000
        )

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

    def _handle_monitor_event(self, event: MonitorEvent) -> None:
        self.printf_queue.put(event.message)
        if event.status_bar_message:
            self.status.showMessage(event.status_bar_message)

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

    def _log_unsupported_type(self, monitor_type, url, name=None):
        monitor_name = f"[{name}]" if name else ""
        readable_type = (
            monitor_type if monitor_type not in (None, "") else self._translate("<空>")
        )
        message = self._translate(
            "监控项{monitor_name}类型 '{monitor_type}' 未被支持，URL: {url}"
        ).format(
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

    def _handle_monitors_saved(self, monitors):
        try:
            configuration.write_monitor_list(monitors)
        except Exception as exc:
            QMessageBox.critical(self.window, self._translate('保存失败'), str(exc))
            self.status.showMessage(
                self._translate('保存失败：{error}').format(error=exc), 5000
            )
        else:
            self.status.showMessage(self._translate('配置已保存'), 4000)
            self._reload_monitors()
            self.ui.show_monitor_page()

    def _reload_monitors(self):
        monitors = configuration.read_monitor_list()
        self.ui.configWizard.load_monitors(monitors)

    def _read_config_timezone(self):
        raw_value = configuration.get_timezone()
        try:
            return int(str(raw_value).strip())
        except (TypeError, ValueError):
            return 0

    def _update_timezone_display(self):
        self.ui.localTimeGroupBox.setTitle(
            self._translate('本地时间（时区：{offset}）').format(offset=self.time_zone)
        )
        self.ui.utcTimeGroupBox.setTitle(self._translate('UTC 时间'))

    def on_close(self) -> None:
        if self.scheduler:
            self.scheduler.stop()
        self._stop_periodic_monitors()

    def _build_monitor_item(self, monitorInfo):
        if isinstance(monitorInfo, configuration.MonitorItem):
            return monitorInfo

        name = monitorInfo.get("name")
        url = monitorInfo.get("url")
        if not name or not url:
            self.printf_queue.put(self._translate("监控项配置缺少名称或地址"))
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
                self._translate("监控项[{name}]的周期配置无效: {value}").format(
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


class toolsetWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)
        from ui.theme import ThemeManager, teams_dark, teams_light

        self.theme_manager = ThemeManager()
        self.theme_manager.register_many((teams_light, teams_dark))
        self.theme_manager.apply_theme(teams_light.name)
        self.controller = MainWindowController(self, self.ui, self.theme_manager)

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            controller = super().__getattribute__("controller")
            if hasattr(controller, item):
                return getattr(controller, item)
            raise

    def perform_task(self, *args, **kwargs):  # type: ignore[override]
        if hasattr(self, "controller"):
            return self.controller.perform_task(*args, **kwargs)

        fallback = MainWindowController.__new__(MainWindowController)
        fallback.printf_queue = queue.Queue()
        fallback.status = _SilentStatusBar()
        return MainWindowController.perform_task(fallback, *args, **kwargs)

    def closeEvent(self, event):
        self.controller.on_close()
        super().closeEvent(event)


if __name__ == '__main__':
    log_root = Path(configuration.get_logdir())
    folder = log_root / "Log"
    configDir = log_root / "Config"

    folder.mkdir(parents=True, exist_ok=True)
    if not configDir.exists():
        configDir.mkdir(parents=True, exist_ok=True)
        configuration.writeconfig(str(configDir))
    elif not (configDir / "Config.ini").exists():
        configuration.writeconfig(str(configDir))

    print("folder:", folder)
    print("configDir:", configDir)
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = toolsetWindow()
    mainWindow.show()
    sys.exit(app.exec_())
