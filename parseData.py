# -*- codeing = utf-8 -*-
# @Time : 2023/4/10 14:37
# @Author: weijia
# @File : parseData.py
# @Software: PyCharm

import json
import xml.etree.ElementTree as ET
import requests

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
    else:
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


def parse_phase_continuity(target:str, dataString:str):
    target_number = int(configuration.get_targetnum(target))
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

# url = 'http://101.42.254.16:6741/PSA/Services/GetPhaseContinuity?region=China.Wuxi&format=xml'
# response = requests.get(url)
# if response.status_code == 200:
#     print(f"GET request to {url} successful")
#     num = parse_phase_continuity('Wuxi', response.text)
#     print("parse_phase_continuity(data):", num)