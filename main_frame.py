# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:22 p.m.
# @Author: Weijia Zhao
# @File : main_frame.py

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog
import threading
import datetime
import os
import time
import sys
from typing import List, Dict, Tuple

from GUI_windows_v2 import MainWindow
import configuration
import parse_data
import monitor
import send_email
import log_recorder

switch_status = True
printf = []


class monitor_window(QtWidgets.QMainWindow, MainWindow):
    global switch_status
    global printf

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
        self.setupUi(self)
        self.status = self.statusBar()
        self.status.showMessage('>>Initializing...', 2000)

        title: List[str, str] = configuration.read_general()

        self.setWindowTitle(f'{title[0]} - v{title[1]}')
        self.switchButton.clicked.connect(self.start_monitor)
        self.configButton.clicked.connect(self.configuration)
        self.locationButton.clicked.connect(self.set_location)
        # auto_update: int = configuration.read_log_settings()
        # if auto_update == 1:
        #     self.get_expected_targets()
        self.read_config()

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
            result: Tuple[int, str] = monitor.monitor_get(
                self.parse_network_address(url))
            expected_num: int = parse_data.parse_expected_targets(result[1])
            configuration.set_targetnum(region, expected_num)

            # Log/Output————————————————————————————————
            printf.append(f"{region} - Expected Targets is {expected_num}")
            # entry to Log
            log_recorder.record_to_log(
                "Get Expected Targets",
                f"{region} Expected Target Signal Number is {expected_num}")
        return

    def read_config(self) -> None:
        """
        Read the monitor list from the configuration file and output the
        configuration information.

        :return: None
        """
        monitor_list: List[Dict[str, str]] = configuration.read_monitor_list()
        printf.append(f"Read {len(monitor_list)} Monitor Items as following:")
        log_recorder.record_to_log("Start Monitor",
                                   f"Read {len(monitor_list)} Monitor Items")
        for i in range(len(monitor_list)):
            name: str = monitor_list[i]['name']
            url: str = monitor_list[i]['url']
            interval: str = monitor_list[i]['interval']
            mtype: str = monitor_list[i]['type']

            # Log/Output————————————————————————————————
            printf.append(
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
            monitor_list: List[Dict[str,
                                    str]] = configuration.read_monitor_list()
            self.run_with_threads(len(monitor_list), monitor_list)

            self.switchButton.setText('Close')
            self.status.showMessage('>>>Runing...')
            switch_status = False
        elif switch_status is False:
            sys.exit()

    def configuration(self) -> None:
        """
        Open the configuration file for the monitor list in the default text
        editor of the system.

        This function will open the configuration file specified in the
        configuration file in the default text editor of the system. The user
        can then edit the configuration file to change the monitor items.

        :return: None
        """
        dir: str = f'{configuration.get_log_dir()}Config/MonitorList.ini'
        # dir2: str = f'./mail_sample/OutageNotificationMailSample.html'
        print(dir)
        command = f'start "" "{dir}"'
        os.system(command)

    def set_location(self) -> None:
        """
        Opens a dialog box to let the user set the time zone, then update the
        time zone displayed in the local time group box and save the time zone
        to the configuration file.

        :return: None
        """
        time_zone: int = int(configuration.get_timezone())
        time_zone, ok = QInputDialog.getInt(
            self, "Enter time zone", "Please enter your time zone (integer):",
            time_zone, -12, 14, 1)
        self.localTimeGroupBox.setTitle(f'Local Time(Time Zone:{time_zone})')
        configuration.set_timezone(time_zone)

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
        global printf
        time_zone: int = int(configuration.get_timezone())
        # current_time = QTime.currentTime().toString("Y-M-D hh:mm:ss")
        utc_time: datetime.datetime = datetime.datetime.utcnow()
        current_time: datetime.datetime = datetime.datetime.utcnow(
        ) + datetime.timedelta(hours=time_zone)
        self.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))
        while len(printf) > 0:
            for i in printf:
                self.monitorBrowser.append(i)  # show information in monitor
                self.cursot = self.monitorBrowser.textCursor()
                self.monitorBrowser.moveCursor(self.cursot.End)
            printf.clear()
            QtWidgets.QApplication.processEvents()

    def perform_task(self, url: str, request_type: str, name: str,
                     to_addrs: str) -> Tuple[bool, str]:
        """
        Perform a request to the specified url with the specified request type.

        Args:
            url (str): The url to request.
            request_type (str): The type of request to make, one of "GET",
            "POST", or "SERVER".
            name (str): The name of the request.
            to_addrs (str): The email to send result to.

        Returns:
            Tuple[bool, str]: A tuple  containing the result of the request as
            a boolean and a string describing the result.
        """

        def handle_request(result: Tuple[bool, str]) -> None:
            """
            Handle the request result by printing and potentially logging it.

            Args:
                result (tuple[bool, str]): A tuple containing the result of the
                request as a boolean and a string describing the result.
            """
            print(f"{request_type.upper()}-Result: {result}")
            # TODO: add logging logic if needed
            log_recorder.record_to_log(request_type, f"Result: {result}")

        # Dictionary mapping request types to functions
        request_functions = {
            "GET": monitor.monitor_get,
            "POST": lambda url: monitor.monitor_post(
                url, "1"
            ),  # Assuming "1" is a fixed parameter for POST requests
            "SERVER": monitor.monitor_server
        }

        # Perform the request using the appropriate function
        request_func = request_functions.get(
            request_type, lambda _: (False, "Unknown request type"))
        result = request_func(url)

        # Handle the result
        handle_request(result)
        return result

    # format url
    def parse_network_address(self, address: str) -> Tuple[str, int, str]:
        """
        Parse a network address into its components.

        Parameters:
            address (str): The network address to be parsed.

        Returns:
            Tuple[str, int, str]: A tuple of (url, port, suffix) where url is the base URL,
            port is the port number (default to 80 if not specified), and suffix is the path after the hostname.

        """
        # Remove protocol prefix
        if address.startswith("http://"):
            url_port_suffix = address[len("http://"):]
        elif address.startswith("https://"):
            url_port_suffix = address[len("https://"):]
        else:
            url_port_suffix = address

        # Split URL into base (with potential port) and suffix at the first '/'
        url_with_port, *suffix_parts = url_port_suffix.split('/', 1)
        suffix = suffix_parts[0] if suffix_parts else ''

        # Extract port number if specified; otherwise, set it to None
        url, *port_parts = url_with_port.split(':')
        port = int(port_parts[0]) if port_parts else None

        print('url:', url, '\nport:', port, '\nsuffix:', suffix)
        return url, port, suffix

    def run_periodically(self, monitor_info: Dict[str, str]) -> None:
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
        time_zone = int(configuration.get_timezone())
        i = 1
        last_status = True
        while True:
            timenow = datetime.datetime.utcnow() + datetime.timedelta(
                hours=time_zone)
            # Get the configuration
            name = monitor_info['name']
            url = monitor_info['url']
            mtype = monitor_info['type']
            interval = int(monitor_info['interval'])
            to_addrs = monitor_info['email']

            # format the url, port, suffix
            url = self.parse_network_address(url)
            # start the monitoring process, return value: bool, string
            result = self.perform_task(url, mtype, name, to_addrs)

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

            if type(result[1]).__name__ == 'list':
                remark = len(result[1])
                output = [timenow, name, mtype, url, interval,
                          len(result[1])] + result[1]
            else:
                remark = result[1]
                output = [timenow, name, mtype, url, interval, result[1]]

            output = response_code + output
            # output = response_code.append(output)
            print(">>output:", output)

            # process the result
            if response_code[0] == 1:
                print(
                    f"{i}: {timenow} - {name} - Status: Service/Server is running well"
                )
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} - {name} - Status: Service/Server Available, Remark: {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name}- Type: {mtype} - url: {url} - Interval: {interval} s",
                    f">>{timenow} - {name} - Service/Server Available, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 2:
                send_email.send_email(
                    f"{timenow}: The {name} service were restored!",
                    f"{name} Service Restored\nRestored Time: {timenow}\nRemark: {remark}",
                    to_addrs)
                print(
                    f"{i}: {timenow} - {name} - Status: Service/Server were restored"
                )
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} - {name} - Status: Service/Server were restored, {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url} - Interval: {interval}s",
                    f">>{timenow} - {name} - Service/Server were restored, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 3:
                send_email.send_email(
                    f"{timenow}: The {name} server outage!",
                    f"{name} Outage\nTime: {timenow}\nRemark: {remark}",
                    to_addrs)
                print(
                    f"{i}: {timenow} - {name} - Status: Service/Server Outage")
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} - {name} - Status: Service/Server Outage, {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url} - Interval: {interval}s",
                    f">>{timenow} - {name} - Service/Server Outage, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 4:
                send_email.send_email(
                    f"{timenow}: The {name} server outage!",
                    f"{name} Continuous Server/Service Outage\nSignal outage occurred: {timenow}\nRemark: {remark}",
                    to_addrs)
                print(
                    f"\n{i}: {timenow} - {name} - Status: Continuous Server/Service Outage"
                )
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} - {name} - Status: Continuous Server/Service Outage, {remark}"
                )

                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url} - Interval: {interval}s",
                    f">>{timenow} - {name} - Continuous Server/Service Outage, Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            print(f"\nWaiting for {interval} s")
            i += 1
            last_status = result[0]
            time.sleep(interval)

    # Create threads for each monitor
    def run_with_threads(self, num_threads: int,
                         monitor_list: List[Dict[str, str]]) -> None:
        """
        Create and start a thread for each monitor in the list.

        Args:
            num_threads (int): The number of threads to create.
            monitor_list (List[Dict[str, str]]): A list of dictionaries
            containing information about each monitor.

        Returns:
            None
        """
        for i in range(num_threads):
            monitor_info = monitor_list[i]
            t = threading.Thread(name=monitor_info['name'],
                                 target=self.run_periodically,
                                 args=(monitor_info, ))
            t.setDaemon(True)
            t.start()


if __name__ == '__main__':
    folder = os.path.expanduser('API Monitor/Log')
    config_dir = os.path.expanduser("API Monitor/Config")
    mailSampleDir = os.path.expanduser("API Monitor/MailSample")

    print("folder:", folder)
    print("config_dir:", config_dir)
    print("mailSampleDir:", mailSampleDir)

    # Determines if a folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
    if not os.path.exists(mailSampleDir):
        os.makedirs(mailSampleDir)
        configuration.write_mailSample(mailSampleDir)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        configuration.write_config(config_dir)
    if not os.path.exists(str(config_dir + "/Config.ini")):
        configuration.write_config(config_dir)
    if not os.path.exists(str(config_dir + "/MonitorList.ini")):
        configuration.write_monitor_list(config_dir)
    time.sleep(2.9)

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = monitor_window()
    mainWindow.show()
    sys.exit(app.exec_())
