# -*- codeing = utf-8 -*-
# @Time : 2023-02-16 3:37 p.m.
# @Author: weijiazhao
# @File : logRecorder.py
# @Software: PyCharm
import datetime
import csv
from pathlib import Path

import configuration


def _now_with_timezone():
    try:
        timezone = int(configuration.get_timezone())
    except (TypeError, ValueError):
        timezone = 0
    utc_now = datetime.datetime.utcnow()
    return utc_now + datetime.timedelta(hours=timezone)


def _ensure_log_folder() -> Path:
    folder = Path(configuration.get_logdir()) / "Log"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _csv_header() -> list:
    header_template = configuration.get_template_manager().get_template(
        "log", "csv_header", configuration.get_language()
    )
    return [column.strip() for column in header_template.split(",") if column.strip()]


def record(action: str, log):
    chinaDateTime = _now_with_timezone()
    folder = _ensure_log_folder()

    log_path = folder / f"log-{chinaDateTime.strftime('%Y%m%d')}.txt"
    log_timestamp = chinaDateTime.strftime('%Y-%m-%d %H:%M:%S')
    entry = configuration.render_template(
        "log",
        "record_entry",
        {
            "log_timestamp": log_timestamp,
            "action": str(action),
            "details": str(log).rstrip("\n"),
        },
    )

    with log_path.open("a", encoding="utf-8") as file:
        file.write(entry.rstrip("\n") + "\n")


def saveToFile(dataString, API):
    folder = _ensure_log_folder()

    nowDateTime = _now_with_timezone()
    nowDate = nowDateTime.strftime("%Y%m%d")

    filename = folder / f"{API}_{nowDate}.csv"
    header = _csv_header()
    row = [str(item) for item in dataString]

    if not filename.exists():
        with filename.open(mode='w', newline='', encoding='utf8') as cf:
            wf = csv.writer(cf)
            wf.writerow(header)
            wf.writerow(row)
    else:
        with filename.open(mode='a', newline='', encoding='utf8') as cfa:
            wf = csv.writer(cfa)
            wf.writerow(row)

# b = ['aaa','vvvv','ssss','wwww','gggg','qqqq','rrrr','yyyy']
# saveToFile(b, 'test')