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

from GUI_windows_v2 import MainWindow
import configuration
import parse_data
import api_monitor
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
        the json file.

        :return: None
        """
        super().__init__()
        self.setupUi(self)
        self.status = self.statusBar()
        self.status.showMessage('>>Initializing...', 2000)

        title: list[str, str] = configuration.read_general()

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
        server_list: list[tuple[str, str]] = configuration.get_server_ip()
        time.sleep(0.3)
        for item in server_list:
            region: str = item[0].title()
            ip_address: str = item[1]
            url: str = (
                ip_address +
                f":6265/PSA/Services/GetExpectedTargets?region=China.{region.split('-')[0]}&format=XML&filter=All"
            )
            result: tuple[int, str] = api_monitor.monitor_get(
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
        monitorList: list[dict[str, str]] = configuration.read_monitor_list()
        printf.append(f"Read {len(monitorList)} Monitor Items as following:")
        log_recorder.record_to_log("Start Monitor",
                                   f"Read {len(monitorList)} Monitor Items")
        for i in range(len(monitorList)):
            name: str = monitorList[i]['name']
            url: str = monitorList[i]['url']
            interval: str = monitorList[i]['interval']
            mtype: str = monitorList[i]['type']

            # Log/Output————————————————————————————————
            printf.append(
                f"{i+1}.{name} - Type:{mtype} - url:{url} - Interval:{interval} s"
            )
            # entry to Log
            log_recorder.record_to_log(
                "Read Configuration",
                f"{i+1}.{name} - Type:{mtype} - url:{url} - Interval:{interval} s"
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
            monitor_list: list[dict[str,
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
        dir: str = f'{configuration.get_logdir()}Config/MonitorList.ini'
        # dir2: str = f'./mail_sample/OutageNotificationMailSample.html'
        print(dir)
        os.system(f"start {dir}")

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
        Update the clock displayed in the local time group box and utc time label.

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
                     email: str) -> list[bool, str]:
        """
        Perform a request to the specified url with the specified request type.

        Args:
            url (str): The url to request.
            request_type (str): The type of request to make, one of "GET", "POST", or "SERVER".
            name (str): The name of the request.
            email (str): The email to send result to.

        Returns:
            list[bool, str]: A list containing the result of the request as a boolean and a string describing the result.
        """

        def handle_request(result: tuple[bool, str]) -> None:
            """
            Handle the request result by printing and potentially logging it.

            Args:
                result (tuple[bool, str]): A tuple containing the result of the
                request as a boolean and a string describing the result.
            """
            print(f"{request_type.upper()}-Result: {result}")
            # TODO: add logging logic if needed

        if request_type == "GET":
            result = api_monitor.monitor_get(url)
            if result[0]:
                result = parse_data.parse_data(name, result[1])
            handle_request(result)
            return result
        elif request_type == "POST":
            result = api_monitor.monitor_post(url, "1")
            handle_request(result)
            return result
        elif request_type == "SERVER":
            result = api_monitor.monitor_server(url)
            handle_request(result)
            return result
        else:
            # Handle unknown request type
            handle_request((False, "Unknown request type"))
            return [False, "Unknown request type"]

    # format url
    def parse_network_address(self, address: str) -> list[str, int, str]:
        """
        Parse a network address into its components.

        Parameters:
            address (str): The network address to be parsed.

        Returns:
            list: A list of [url (str), port (int), suffix (str)] where url is
            the url of the network address, port is the port number of the
            network address and suffix is the suffix of the network address
            after the port number.

        """
        # Remove protocol prefix
        if address.startswith("http://"):
            url_port_suffix = address[len("http://"):]
        elif address.startswith("https://"):
            url_port_suffix = address[len("https://"):]
        else:
            url_port_suffix = address

        # Split URL into base and suffix at the first '/'
        # and port if specified
        url_port_match = url_port_suffix.split('/', 1)
        url_port = url_port_match[0]
        suffix = url_port_match[1] if len(url_port_match) > 1 else ''

        # Extract port number if specified
        port_match = url_port.split(':')
        url = port_match[0]
        port = int(port_match[1]) if len(port_match) > 1 else ''

        print('url:', url, '\nport:', port, '\nsuffix:', suffix)
        return [url, port, suffix]

    def run_periodically(self, monitor_info: dict[str, str]) -> None:
        """
        Run the monitoring process in a loop.

        Parameters:
            monitor_info (dict[str, str]): A dictionary containing the
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
            email = monitor_info['email']

            # format the url, port, suffix
            url = self.parse_network_address(url)
            # start the monitoring process, return value: bool, string
            result = self.perform_task(url, mtype, name, email)

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

            # 'StatusCode', 'Status', 'Time', 'Name', 'Type', 'URL', 'Interval', 'Content', 'Remarks'
            output = response_code + output
            # output = response_code.append(output)
            print(">>output:", output)

            # process the result
            if response_code[0] == 1:
                print(
                    f"{i}: {timenow} > {name} > Status: Service/Server is running well"
                )
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} >> {name} >> Status: Service/Server Available, Remark: {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url} - Interval: {interval} s",
                    f">>{timenow} >> {name} >> Service/Server Available >> Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 2:
                send_email.send_email(
                    f"{timenow}: The {name} service were restored!",
                    f"{name} Service Restored\nRestored Time：{timenow}\nRemark: {remark}"
                )
                print(
                    f"{i}: {timenow} >> {name} >> Status: Service/Server were restored"
                )
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} >> {name} >> Status: Service/Server were restored, {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url} - Interval: {interval}s",
                    f">>{timenow} >> {name} >> Service/Server were restored >> Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 3:
                send_email.send_email(
                    f"{timenow}: The {name} server outage!",
                    f"{name} Outage\nTime: {timenow}\nRemark: {remark}")
                print(
                    f"{i}: {timenow} >> {name} >> Status: Service/Server Outage"
                )
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} >> {name} >> Status: Service/Server Outage, {remark}"
                )
                # record to log
                log_recorder.record_to_log(
                    f"{name} - Type: {mtype} - url: {url} - Interval: {interval}s",
                    f">>{timenow} >> {name} >> Service/Server Outage >> Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            elif response_code[0] == 4:
                send_email.send_email(
                    f"{timenow}: The {name} server outage!",
                    f"{name} Continuous Server/Service Outage\nSignal outage occurred: {timenow}\nRemark: {remark}"
                )
                print(
                    f"\n{i}: {timenow} >>> {name} >>> Status: Continuous Server/Service Outage"
                )
                # >>>Log and Output<<<
                printf.append(
                    f"{timenow} >>> {name} >>> Status: Continuous Server/Service Outage, {remark}"
                )

                # record to log
                log_recorder.record_to_log(
                    f"{name} --- Type: {mtype} --- url: {url} --- Interval: {interval}s",
                    f">>{timenow} >> {name} >> Continuous Server/Service Outage >> Remarks: {remark}\n"
                )
                log_recorder.save_to_csv(output, name)

            # if response_code[0] == 1 or response_code[0] == 2:
            #     self.status.showMessage('>>>Runing...')
            # else:
            #     self.status.showMessage(f'{name} Service Outage')
            print(f"\nWaiting for {interval} s")
            i += 1
            last_status = result[0]
            time.sleep(interval)

    # Create threads for each monitor
    def run_with_threads(self, num_threads: int, monitorList: list):
        for i in range(num_threads):
            monitorInfo = monitorList[i]
            t = threading.Thread(name=monitorInfo['name'],
                                 target=self.run_periodically,
                                 args=(monitorInfo, ))
            t.setDaemon(True)
            t.start()


if __name__ == '__main__':
    folder = os.path.expanduser('APIMonitor/Log')
    configDir = os.path.expanduser("APIMonitor/Config")
    mailSampleDir = os.path.expanduser("APIMonitor/MailSample")

    print("folder:", folder)
    print("configDir:", configDir)
    print("mailSampleDir:", mailSampleDir)

    if not os.path.exists(folder):  # Determines if a folder exists
        os.makedirs(folder)
    if not os.path.exists(mailSampleDir):
        os.makedirs(mailSampleDir)
        configuration.write_mailSample(mailSampleDir)
    if not os.path.exists(configDir):
        os.makedirs(configDir)
        configuration.write_config(configDir)
    if not os.path.exists(str(configDir + "/Config.ini")):
        configuration.write_config(configDir)
    if not os.path.exists(str(configDir + "/MonitorList.ini")):
        configuration.write_monitor_list(configDir)
    time.sleep(2.9)

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = monitor_window()
    mainWindow.show()
    sys.exit(app.exec_())
