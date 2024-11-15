# -*- codeing = utf-8 -*-
# @Time : 2023/4/10 14:37
# @Author: weijia
# @File : parseData.py

import json
import xml.etree.ElementTree as ET
import configuration

from typing import Tuple, List, Union


def parse_data(service_type: str, data: str) -> Tuple[bool, str]:
    """
    This function parses the data based on the name and data supplier.

    Parameters:
        service_type (str): The type of the data.
        data (str): The data to be parsed.

    Returns:
        Tuple[bool, str]: A tuple containing the parsed data.
    """
    # TODO: Add more service types here
    if service_type == 'NCTCOG' or service_type == 'CEVE':
        print(f'!!!!Type: {service_type}')
        status = parse_nctcog_ceve(data)
        return status, service_type
        # TODO: Add more service types here
    # elif service_type == 'Wuxi':
    #     print(f'!!!!Type: {service_type}')
    #     status = parse_wuxi_data(data)
    #     return status, service_type
    else:
        print('!!Type: No Match')
        return True, 'GET'


def parse_nctcog_ceve(data_string: str) -> bool:
    """
    Parse the given JSON string and return True if the data is valid.

    Parameters:
        data_string (str): The JSON string to parse.

    Returns:
        bool: True if the data is valid, otherwise False.
    """
    # read the json from string
    try:
        data = json.loads(data_string)
        print("!!!!!!!!!!!!!!data:", data)
        return True
    except json.JSONDecodeError:
        print("Invalid JSON string")
        return False


def parse_wuxi_data(data_string: str) -> Tuple[bool, int]:
    """
    Parse the given JSON string and return True if the number of unique signal
    controllers is less than 1000, False otherwise.

    Parameters:
        data_string (str): The JSON string to parse.

    Returns:
        Tuple[bool, int]: A tuple containing a boolean indicating if the
        number of unique signal controllers is less than 1000, and the number
        of unique signal controllers.
    """
    controler_list: List[str] = []
    # read the json from string
    data = json.loads(data_string)
    signal_controler_id_list = data['Body']['Operation']['SysInfo'][
        'SignalControlerIDList']
    for signal_controler_id in signal_controler_id_list:
        controler_id = signal_controler_id['SignalControlerID']
        controler_list.append(controler_id)
    controler_counter = len(set(controler_list))
    if controler_counter < 1000:
        return False, controler_counter
    elif controler_counter < 1400:
        return False, controler_counter
    else:
        return True, controler_counter


def parse_phase_continuity(
        target_region: str,
        data_string: str) -> Tuple[bool, List[List[Union[str, int]]]]:
    """
    Parse the phase continuity data from the given XML string, and check if
    the number of incomplete phases exceeds the threshold.

    Args:
        target_region (str): The target region to check.
        data_string (str): The XML string containing the phase continuity data.

    Returns:
        Tuple[bool, List[List[Union[str, int]]]]: A tuple containing a boolean
        indicating if the number of incomplete phases exceeds the threshold,
        and a list of lists containing the SCNR, feed phases, and unsupported
        phases for each target.
    """
    target_number = int(configuration.get_targetnum(target_region))
    incomplete_phase = []
    # read the xml from string
    root = ET.fromstring(data_string)
    for target in root.iter('Target'):
        scnr_list = []
        scnr = target.get('scNr')
        feed_phase = target.get('feedPhases')
        unsupported_phase = target.get('unsupportedPhases')
        scnr_list.append(scnr)
        scnr_list.append(feed_phase)
        scnr_list.append(unsupported_phase)
        incomplete_phase.append(scnr_list)
        # print("scnr_list:", scnr_list)
    print("scnr_feedback:", len(incomplete_phase))
    if len(incomplete_phase) > target_number / 1.5:
        return False, incomplete_phase
    elif len(incomplete_phase) > target_number / 2:
        return False, incomplete_phase
    else:
        return True, incomplete_phase


def parse_expected_targets(data_string: str) -> int:
    """
    Parse the expected targets from the XML data.

    Parameters:
        dataString (str): The XML data string to parse.

    Returns:
        int: The number of expected targets parsed from the XML data.
    """
    scnr_list: List[str] = []
    # read the xml from string
    root = ET.fromstring(data_string)
    for target in root.iter('Target'):
        scnr: str = target.get('scNr')
        scnr_list.append(scnr)
    expected_targets_num: int = len(scnr_list)
    print("expected_targets_num:", expected_targets_num)
    return expected_targets_num


def parse_live_targets(target_region: str,
                       data_string: str) -> Tuple[bool, int]:
    """
    Parse the live targets from the XML data.

    Parameters:
        target_region (str): The target region to parse.
        data_string (str): The XML data string to parse.

    Returns:
        Tuple[bool, int]: A tuple containing a boolean indicating if the
        number of live targets exceeds 1.5 times the target number, and the
        number of live targets parsed from the XML data.
    """
    target_region = target_region.title()
    target_number = int(configuration.get_targetnum(target_region))
    print("target_number:", target_number)
    print("target_region:", target_region)
    scnr_list = []
    # read the xml from string
    root = ET.fromstring(data_string)
    for target in root.iter('Target'):
        if target.get('subRegion') == target_region.split('-')[0]:
            scnr = target.get('scNr')
            scnr_list.append(scnr)
    print("scnr_list:", scnr_list)
    live_targets_num = len(scnr_list)
    print("live_targets_num:", live_targets_num)
    if live_targets_num > target_number / 1.5:
        return True, live_targets_num
    elif live_targets_num > target_number / 2:
        return False, live_targets_num
    else:
        return False, live_targets_num
