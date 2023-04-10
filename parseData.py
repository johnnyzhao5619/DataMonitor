# -*- codeing = utf-8 -*-
# @Time : 2023/4/10 14:37
# @Author: weijia
# @File : parseData.py
# @Software: PyCharm

import json
import requests

def parseData(name, data):
    if name == "Wuxi":
        signal_num = parseWuxi(data)
        print("parseWuxi(data):", signal_num)
        return signal_num[0], signal_num[1]
    else:
        return True, "GET"

def parseWuxi(dataString):
    controler_list = []
    data = json.loads(dataString)
    singal_controler_id = data['Body']['Operation']['SysInfo']['SignalControlerIDList']
    for i in range(len(singal_controler_id)):
        controler_id = singal_controler_id[i]['SignalControlerID']
        controler_list.append(controler_id)
    controler_counter = len(list(set(controler_list)))
    # print("controler_list:", len(controler_list))
    # print("controler_counter:", len(controler_counter))
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
#     num = parseWuxi(response.text)
#     print("parseWuxi(data):", num)