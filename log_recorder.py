# -*- codeing = utf-8 -*-
# @Time : 2023-02-16 3:37 p.m.
# @Author: weijia zhao
# @File : log_recorder.py

import datetime
import csv
import os
import configuration
from typing import List, Tuple, Union


def record_to_log(action: str, log: str) -> None:
    """
    Records an action and log message to a log file.

    Args:
        action (str): The action that was performed.
        log (str): The log message to record.

    Returns:
        None
    """
    # timezone: str = configuration.get_timezone()
    # local_Time: datetime.datetime = datetime.datetime.utcnow(
    # ) + datetime.timedelta(hours=int(timezone))

    # folder: str = os.path.expanduser(str(configuration.get_logdir() + 'Log'))
    # if not os.path.exists(folder):
    #     os.makedirs(folder)

    timezone: str = configuration.get_timezone()
    local_time = datetime.datetime.utcnow() + datetime.timedelta(
        hours=int(timezone))

    folder: str = os.path.expanduser(configuration.get_logdir() + 'Log')
    if not os.path.exists(folder):
        os.makedirs(folder)

    log_message = f""">>{local_time}(Timezone: {timezone})--------------------------------------
    >>Action:{action}
    {log}\n"""
    with open(f"{folder}/log-{local_time.strftime('%Y%m%d')}.txt",
              'a',
              encoding='gb18030',
              errors='ignore') as file:
        file.write(log_message)


def save_to_csv(dataString: Union[List[Tuple[int, str, str, str, str, str, str,
                                             str, str]], None],
                API: str) -> None:
    """
    Saves API data to a CSV file.

    Args:
        dataString (Union[List[Tuple[int, str, str, str, str, str, str, str, str]], None]):
            The data to be written to the CSV file. If None, the file is not written to.
            The data is a list of tuples with the following elements:

                * StatusCode: The status code of the API request.
                * Status: The status of the API request.
                * Time: The time of the API request.
                * Name: The name of the API request.
                * Type: The type of the API request.
                * URL: The URL of the API request.
                * Interval: The interval of the API request.
                * Content: The content of the API request.
                * Remarks: The remarks of the API request.
        API (str): The name of the API to save the data for.

    Returns:
        None
    """
    timezone = int(configuration.get_timezone())
    folder = os.path.expanduser(str(configuration.get_logdir() + 'Log'))
    if not os.path.exists(folder):
        os.makedirs(folder)
    nowDateTime = datetime.datetime.utcnow() + datetime.timedelta(
        hours=timezone)
    nowDate = nowDateTime.strftime("%Y%m%d")
    filename = f'{folder}/{API}_{nowDate}.csv'
    if not os.path.exists(filename):
        # Create the file and write the header row
        with open(filename,
                  mode='w',
                  newline='',
                  encoding='gb18030',
                  errors='ignore') as cf:
            wf = csv.writer(cf)
            title = [
                'StatusCode', 'Status', 'Time', 'Name', 'Type', 'URL',
                'Interval', 'Content',
                'Remarks[scNr, feedPhase, unsupportedPhase]'
            ]
            wf.writerow(title)
            # Write the data to the file
            if dataString is not None:
                wf.writerow(dataString)
    elif dataString is not None:
        # Append the data to the file
        with open(filename,
                  mode='a',
                  newline='',
                  encoding='gb18030',
                  errors='ignore') as cfa:
            wf = csv.writer(cfa)
            wf.writerow(dataString)
    else:
        # Do nothing
        pass
