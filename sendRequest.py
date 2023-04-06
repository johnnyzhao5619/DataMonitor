# -*- codeing = utf-8 -*-
# @Time : 2023-02-01 3:52 p.m.
# @Author: weijiazhao
# @File : sendRequest.py
# @Software: PyCharm

import requests

def getInfo(url):
    # params

    # 发送请求
    ask = requests.get(url)
    # print('raw 文本内容:', ask.text)  # raw 文本内容
    # print('状态码:', ask.status_code)  # 状态码
    # print('dict:', ask.headers)  # dict
    # print('key:', ask.headers['Date'])  # key
    # print('RequestsCookieJar:', ask.cookies)  # RequestsCookieJar

    return ask.status_code, ask.text


def getPage(url):
    try:
        response = requests.get(url)

    except requests.exceptions.ConnectionError as e:
        return 0, 'Connection Error'
    except requests.exceptions.ChunkedEncodingError as e:
        return 0, 'Chunked Encoding Error'
    except:

        return 0, 'An Unknow Error Happened'
    else:
        if response.status_code == 200:

            return 200, response.text
        else:

            return response.status_code, response.reason

# url = 'http://49.232.78.244:6741/PSA/Services/GetMonthlyAccuracyReport?region=China.Nanjing&startDate=20230201&numDays=3&format=CSV&viewOptions=ShowScore|ShowConfidence|ShowHours'
# CSV = getInfo(url, 'CSV')
#

# getPage("http://219.239.83.74:7429/PSA/Services/GetTargetedSPaT?target=Nanjing:2066.1&format=JSON")
# getPage("http://www.baidus.s/rul")