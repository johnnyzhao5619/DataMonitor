# -*- codeing = utf-8 -*-
# @Time : 2023/4/10 14:37
# @Author: weijia
# @File : parseData.py
# @Software: PyCharm

import json
import xml.etree.ElementTree as ET
import configuration


def parse_data(name, data):
    region, servicetype = name.split(' ', 1)
    print("region, servicetype:", region, servicetype)
    if servicetype == 'Data Provider' and region == 'Wuxi':
        signal_num = parse_wuxi(data)
        return signal_num[0], signal_num[1]
    elif servicetype == 'Phase Continuity':
        signal_num = parse_phase_continuity(region, data)
        return signal_num[0], signal_num[1]
    elif servicetype == 'Live Target':
        print('!!Type: Live Target')
        live_signal_num = parse_live_targets(region, data)
        return live_signal_num[0], live_signal_num[1]
    else:
        print('!!Type: No Match')
        return True, "GET"

def parse_wuxi(dataString):
    controler_list = []
    data = json.loads(dataString)
    singal_controler_id = data['Body']['Operation']['SysInfo']['SignalControlerIDList']
    for i in range(len(singal_controler_id)):
        controler_id = singal_controler_id[i]['SignalControlerID']
        controler_list.append(controler_id)
    controler_counter = len(list(set(controler_list)))
    if controler_counter < 1000:
        return False, controler_counter
    elif controler_counter < 1400:
        return False, controler_counter
    else:
        return True, controler_counter

# url = 'http://36.155.95.59:28080/JKS_Server/SysInfo'
# response = requests.get(url)
# if response.status_code == 200:
#     print(f"GET request to {url} successful")
#     num = parse_wuxi(response.text)
#     print("parse_wuxi(data):", num)




def parse_phase_continuity(target_region:str, dataString:str):
    target_number = int(configuration.get_targetnum(target_region))
    incomplete_phase = []
    # 从字符串中读取xml
    root = ET.fromstring(dataString)
    for target in root.iter('Target'):
        scnr_list = []
        scnr = target.get('scNr')
        feedPhase = target.get('feedPhases')
        unsupportedPhase = target.get('unsupportedPhases')
        scnr_list.append(scnr)
        scnr_list.append(feedPhase)
        scnr_list.append(unsupportedPhase)
        incomplete_phase.append(scnr_list)
        # print("scnr_list:", scnr_list)
    print("scnr_feedback:", len(incomplete_phase))
    if len(incomplete_phase) > target_number/1.5:
        return False, incomplete_phase
    elif len(incomplete_phase) > target_number/2:
        return False, incomplete_phase
    else:
        return True, incomplete_phase

def parse_expected_targets(dataString: str):
    scnr_list = []
    # 从字符串中读取xml
    root = ET.fromstring(dataString)
    for target in root.iter('Target'):
        scnr = target.get('scNr')
        scnr_list.append(scnr)
    expected_targets_num = len(scnr_list)
    print("expected_targets_num:", expected_targets_num)
    return expected_targets_num

def parse_live_targets(target_region: str, dataString: str):
    target_region = target_region.title()
    target_number = int(configuration.get_targetnum(target_region))
    print("target_number:", target_number)
    print("target_region:", target_region)
    scnr_list = []
    # 从字符串中读取xml
    root = ET.fromstring(dataString)
    for target in root.iter('Target'):
        if target.get('subRegion') == target_region.split('-')[0]:
            scnr = target.get('scNr')
            scnr_list.append(scnr)
    print("scnr_list:",scnr_list)
    live_targets_num = len(scnr_list)
    print("live_targets_num:", live_targets_num)
    if live_targets_num > target_number/1.5:
        return True, live_targets_num
    elif live_targets_num > target_number/2:
        return False, live_targets_num
    else:
        return False, live_targets_num

# url_1 = 'http://101.42.254.16:6265/PSA/Services/GetExpectedTargets?region=China.Wuxi&format=XML&filter=All'
# url_2 = 'http://101.42.254.16:6265/PSA/Services/GetLiveTargets?region=China.Wuxi&format=XML&filter=All'
# response_1 = requests.get(url_1)
# if response_1.status_code == 200:
#     print(f"GET request to {url_1} successful")
#     num = parse_expected_targets('Wuxi', response_1.text)
#     print("parse_expected_targets(data):", num)
#
# response_2 = requests.get(url_2)
#
# time.sleep(2)
# if response_2.status_code == 200:
#     print(f"GET request to {url_2} successful")
#     num = parse_live_targets('Wuhan', response_2.text)
#     print("parse_live_targets(data):", num)

