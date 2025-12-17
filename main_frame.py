# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:22 p.m.
# @Author: Weijia Zhao
# @File : main_frame.py

from PyQt5 import QtWidgets
import threading
import datetime
import os
import time
import sys
from typing import List, Dict, Tuple
import json
from collections import deque

from gui import MainWindow
import configuration
import parse_data
import monitor
import send_email
import log_recorder
from config_dialog import ConfigDialog

switch_status = True
printf = deque(maxlen=1000)
printf_lock = threading.Lock()


def push_log(message: str) -> None:
    with printf_lock:
        printf.append(message)


def pop_all_logs() -> list:
    with printf_lock:
        logs = list(printf)
        printf.clear()
    return logs


class monitor_window(QtWidgets.QMainWindow, MainWindow):

    def __init__(self) -> None:
        """
        Initialize the main window of the application.

        This function will initialize the main window with UI components and
        set up the connections between buttons and their corresponding
        functions.
        It will also set the title of the window based on the configuration in
        the Config.ini file.

        :return: None
        """
        super().__init__()
        configuration.ensure_defaults()
        self.setupUi(self)
        self.status = self.statusBar()
        self.status.showMessage('Initializing...', 2000)
        self.stop_event = threading.Event()
        self.threads = []
        self.debug = os.getenv("API_MONITOR_DEBUG", "0") == "1"

        title: List[str, str] = configuration.read_general()

        self.setWindowTitle(f'{title[0]} - v{title[1]}')
        self.switchButton.clicked.connect(self.start_monitor)
        self.reloadConfigButton.clicked.connect(self.reload_configuration)
        self.clearLogButton.clicked.connect(self.clear_logs)
        self.copyLogButton.clicked.connect(self.copy_logs)
        self.settingsButton.clicked.connect(self.open_settings)
        # auto_update: int = configuration.read_log_settings()
        # if auto_update == 1:
        #     self.get_expected_targets()
        self.read_config()
        self._init_window_size()

    def _init_window_size(self) -> None:
        """
        Set initial window size based on available screen geometry to improve
        cross-resolution experience.
        """
        screen = QtWidgets.QApplication.primaryScreen()
        if not screen:
            return
        geom = screen.availableGeometry()
        target_width = max(720, int(geom.width() * 0.6))
        target_height = max(500, int(geom.height() * 0.6))
        self.resize(target_width, target_height)

    def get_expected_targets(self) -> None:
        """
        Get expected target signal numbers from XML files.

        This function will get the expected target signal numbers for each
        region from the servers specified in the configuration file. It will
        then save the numbers to the configuration file and log them to the
        log file.

        :return: None
        """
        server_list: List[Tuple[str, str]] = configuration.get_server_ip()
        time.sleep(0.3)
        for item in server_list:
            region: str = item[0].title()
            ip_address: str = item[1]
            url: str = (
                ip_address +
                f":6265/PSA/Services/GetExpectedTargets?region=China.{region.split('-')[0]}&format=XML&filter=All"
            )
            parsed_address = self.parse_network_address(url)
            result = monitor.monitor_get(parsed_address)
            if not result[0]:
                push_log(
                    f"{region} - Expected Targets fetch failed: {result[1]}")
                continue
            expected_num: int = parse_data.parse_expected_targets(
                result[1].get('body', ''))
            configuration.set_targetnum(region, expected_num)

            push_log(f"{region} - Expected Targets is {expected_num}")
            # entry to Log
            log_recorder.record_to_log(
                "Get Expected Targets",
                f"{region} Expected Target Signal Number is {expected_num}")
        return

    def reload_configuration(self) -> None:
        """
        Reload monitor list from configuration with basic validation.
        """
        try:
            self.read_config()
            title: List[str, str] = configuration.read_general()
            self.setWindowTitle(f'{title[0]} - v{title[1]}')
            self.status.showMessage('Configuration reloaded', 2000)
        except Exception as exc:  # noqa: BLE001
            push_log(f"Reload configuration failed: {exc}")
            self.status.showMessage('Reload configuration failed', 4000)

    def open_settings(self) -> None:
        """
        Open settings dialog and reload configuration if saved.
        """
        dlg = ConfigDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.reload_configuration()

    def clear_logs(self) -> None:
        """
        Clear UI log output and pending buffered logs.
        """
        self.monitorBrowser.clear()
        with printf_lock:
            printf.clear()
        self.status.showMessage('Logs cleared', 1500)

    def copy_logs(self) -> None:
        """
        Copy all logs from the browser to clipboard.
        """
        text = self.monitorBrowser.toPlainText()
        QtWidgets.QApplication.clipboard().setText(text)
        self.status.showMessage('Logs copied to clipboard', 1500)

    def read_config(self) -> None:
        """
        Read the monitor list from the configuration file and output the
        configuration information.

        :return: None
        """
        monitor_list: List[Dict[str, str]] = configuration.read_monitor_list()
        push_log(f"Read {len(monitor_list)} Monitor Items as following:")
        log_recorder.record_to_log("Start Monitor",
                                   f"Read {len(monitor_list)} Monitor Items")
        for i in range(len(monitor_list)):
            name: str = monitor_list[i]['name']
            url: str = monitor_list[i]['url']
            interval: str = monitor_list[i]['interval']
            mtype: str = monitor_list[i]['type']

            push_log(
                f"{i+1}.{name} - Type:{mtype} - url:{url} - Interval:{interval}s"
            )
            # entry to Log
            log_recorder.record_to_log(
                "Read Configuration",
                f"{i+1}.{name} - Type:{mtype} - url:{url} - Interval:{interval}s"
            )

    def start_monitor(self) -> None:
        """
        Start or stop the monitor based on the current status of the switch.

        If the switch is currently on, it will start the monitor and switch
        the button to say 'Close'. If the switch is currently off, it will
        stop the monitor and exit the program.

        :return: None
        """
        global switch_status
        if switch_status is True:
            # ensure previous threads fully stopped before new run
            self._stop_threads()
            self.stop_event = threading.Event()
            monitor_list: List[Dict[str,
                                    str]] = configuration.read_monitor_list()
            self.run_with_threads(len(monitor_list), monitor_list,
                                  self.stop_event)

            self.switchButton.setText('Stop')
            self.status.showMessage('Monitoring...')
            switch_status = False
        elif switch_status is False:
            self.status.showMessage('Stopping...', 2000)
            self._stop_threads()
            self.switchButton.setText('Monitor')
            self.status.showMessage('Stopped', 2000)
            switch_status = True

    def _stop_threads(self) -> None:
        """
        Signal all monitor threads to stop and wait for exit.
        """
        if not self.threads:
            return
        self.stop_event.set()
        for t in self.threads:
            t.join(timeout=5.0)
        self.threads = []

    def update_clock(self) -> None:
        """
        Update the clock displayed in the local time group box and utc time.

        This function will get the current time in the specified time zone and
        update the clock displayed in the local time group box. It will also
        update the utc time label. The function will also check if there are
        any messages in the printf list and display them in the monitor
        browser if there are.

        :return: None
        """
        time_zone: int = int(configuration.get_timezone())
        # current_time = QTime.currentTime().toString("Y-M-D hh:mm:ss")
        utc_time: datetime.datetime = datetime.datetime.utcnow()
        current_time: datetime.datetime = datetime.datetime.utcnow(
        ) + datetime.timedelta(hours=time_zone)
        self.localTimeGroupBox.setTitle(
            f'Local Time (UTC Offset: {time_zone})')
        self.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))
        logs = pop_all_logs()
        for log in logs:
            self.monitorBrowser.append(log)  # show information in monitor
            self.cursot = self.monitorBrowser.textCursor()
            if self.autoScrollCheckBox.isChecked():
                self.monitorBrowser.moveCursor(self.cursot.End)
            else:
                self.status.showMessage(
                    'New logs available (auto scroll off)', 1500)
        if logs:
            QtWidgets.QApplication.processEvents()

    def perform_task(self, url: Dict[str, object], request_type: str,
                     name: str, to_addrs: str,
                     payload: object = "",
                     headers: Dict[str, str] = None,
                     use_json: bool = False) -> Tuple[bool, dict]:
        """
        Perform a request to the specified url with the specified request type.

        Args:
            url (Dict[str, object]): 标准化后的地址信息。
            request_type (str): The type of request to make, one of "GET",
            "POST", or "SERVER".
            name (str): The name of the request.
            to_addrs (str): The email to send result to.

        Returns:
            Tuple[bool, dict]: (是否成功, 详情字典)。
        """

        def handle_request(result: Tuple[bool, str]) -> None:
            """
            Handle the request result by printing and potentially logging it.

            Args:
                result (tuple[bool, str]): A tuple containing the result of the
                request as a boolean and a string describing the result.
            """
            if self.debug:
                print(f"{request_type.upper()}-Result: {result}")

        # Dictionary mapping request types to functions
        request_functions = {
            "GET": lambda addr: monitor.monitor_get(addr, headers),
            "POST": lambda addr: monitor.monitor_post(addr, payload, headers,
                                                      use_json),
            "SERVER": monitor.monitor_server
        }

        # Perform the request using the appropriate function
        request_func = request_functions.get(
            request_type, lambda _: (False, {"message": "Unknown request type"}))
        result = request_func(url)

        # Handle the result
        handle_request(result)
        return result

    # format url
    def parse_network_address(self, address: str) -> Dict[str, object]:
        """
        Parse a network address into its components.

        Parameters:
            address (str): The network address to be parsed.

        Returns:
            Dict[str, object]: 标准化的地址信息（scheme/host/port/path/url）。

        """
        from urllib.parse import urlparse

        if not address.startswith("http://") and not address.startswith(
                "https://"):
            address = "http://" + address
        parsed = urlparse(address)
        scheme = parsed.scheme or "http"
        host = parsed.hostname or ""
        port = parsed.port
        path = parsed.path or ""
        if parsed.query:
            path = f"{path}?{parsed.query}"

        normalized = monitor._normalize_address((host, port, path, scheme))
        return normalized

    def run_periodically(self, monitor_info: Dict[str, str],
                         stop_event: threading.Event) -> None:
        """
        Run the monitoring process in a loop.
        Parameters:
            monitor_info (Dict[str, str]): A dictionary containing the
                configuration information of the monitor, including the
                name, url, type and interval of the monitor, the email
                address to send the notification to.
        Returns:
            None

        """
        i = 1
        last_status = True
        while not stop_event.is_set():
            time_zone = int(configuration.get_timezone())
            timenow = datetime.datetime.utcnow() + datetime.timedelta(
                hours=time_zone)
            # Get the configuration
            name = monitor_info['name']
            url = monitor_info['url']
            mtype = monitor_info['type']
            interval = int(monitor_info['interval'])
            to_addrs = monitor_info['email']
            payload = monitor_info.get('payload', '')
            headers = monitor_info.get('headers', {})
            use_json = False
            try:
                # 如果 payload 是合法 JSON，则转为对象并标记为 JSON 请求
                payload_obj = json.loads(payload)
                payload = payload_obj
                use_json = True
            except Exception:
                # 非 JSON 字符串，按原样发送
                pass
            if use_json and headers is not None and isinstance(headers, dict):
                if not any(k.lower() == "content-type"
                           for k in headers.keys()):
                    headers = {**headers, "Content-Type": "application/json"}

            # format the url, port, suffix
            url = self.parse_network_address(url)
            # start the monitoring process, return value: bool, string
            result = self.perform_task(url, mtype, name, to_addrs, payload,
                                       headers, use_json)

            # GET 类型增加数据解析校验（仅针对已支持的服务）
            if result[0] and mtype == "GET" and name in ("NCTCOG", "CEVE"):
                parse_ok, parse_label = parse_data.parse_data(
                    name, result[1].get('body', '') if isinstance(
                        result[1], dict) else '')
                if not parse_ok:
                    result = (False, {
                        'message': f'Parse failed: {parse_label}',
                        'url': url.get('url')
                    })

            # when the result is True and the last status is True
            # the server/service is running well.
            # no action
            if result[0] is True and result[0] == last_status:
                response_code = [1, 'Available']

            # When the result is True and the last status is False
            # the server/service has been restored.
            # send a 'restored' email.
            elif result[0] is True and result[0] != last_status:
                response_code = [2, 'Restored']

            # When the result is False and differs from the previous status
            # the server/service in an outage state.
            # send a outage alert.
            elif result[0] is False and result[0] != last_status:
                response_code = [3, 'Outage']

            # When the result is False and consistent with the previous status
            # the server/service in an outage state.
            elif result[0] is False and result[0] == last_status:
                response_code = [4, 'Outage']

            details = result[1] if isinstance(result[1], dict) else {}
            remark = details.get('message') or details.get(
                'status_code') or 'No detail'
            content = details.get('body') or ''
            output = [
                response_code[0], response_code[1], timenow, name, mtype,
                url.get('url'), interval, content, remark
            ]
            if self.debug:
                print("debug output:", output)

            # process the result
            if response_code[0] == 1:
                # >>>Log and Output<<<
                push_log(
                    f"{timenow} - {name} - Status: Service/Server Available, Remark: {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name}- Type: {mtype} - url: {url.get('url')} - Interval: {interval} s",
                    f">>{timenow} - {name} - Service/Server Available, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 2:
                subject, body = send_email.format_event_email(
                    'restored', name, timenow, remark)
                send_email.send_email(subject, body, to_addrs)
                # >>>Log and Output<<<
                push_log(
                    f"{timenow} - {name} - Status: Service/Server were restored, {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url.get('url')} - Interval: {interval}s",
                    f">>{timenow} - {name} - Service/Server were restored, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 3:
                subject, body = send_email.format_event_email(
                    'outage', name, timenow, remark)
                send_email.send_email(subject, body, to_addrs)
                # >>>Log and Output<<<
                push_log(
                    f"{timenow} - {name} - Status: Service/Server Outage, {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url.get('url')} - Interval: {interval}s",
                    f">>{timenow} - {name} - Service/Server Outage, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 4:
                # >>>Log and Output<<<
                push_log(
                    f"{timenow} - {name} - Status: Continuous Server/Service Outage, {remark}"
                )

                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url.get('url')} - Interval: {interval}s",
                    f">>{timenow} - {name} - Continuous Server/Service Outage, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            if self.debug:
                print(f"debug waiting: {interval} s")
            i += 1
            last_status = result[0]
            if stop_event.wait(interval):
                break

    # Create threads for each monitor
    def run_with_threads(self, num_threads: int,
                         monitor_list: List[Dict[str, str]],
                         stop_event: threading.Event) -> None:
        """
        Create and start a thread for each monitor in the list.

        Args:
            num_threads (int): The number of threads to create.
            monitor_list (List[Dict[str, str]]): A list of dictionaries
            containing information about each monitor.

        Returns:
            None
        """
        self.threads = []
        for i in range(num_threads):
            monitor_info = monitor_list[i]
            t = threading.Thread(name=monitor_info['name'],
                                 target=self.run_periodically,
                                 args=(monitor_info, stop_event))
            t.setDaemon(True)
            t.start()
            self.threads.append(t)


if __name__ == '__main__':
    configuration.ensure_defaults()
    time.sleep(0.1)

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = monitor_window()
    mainWindow.show()
    sys.exit(app.exec_())
