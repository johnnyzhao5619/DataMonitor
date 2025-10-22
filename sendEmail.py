# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:56 p.m.
# @Author: weijiazhao
# @File : sendEmail.py
# @Software: PyCharm

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple

import configuration


ALERT_SUBJECT_TEMPLATE = "Outage Alert"
RECOVERY_SUBJECT_TEMPLATE = "Outage Recovery"


def build_outage_alert_message(service_name: str, timestamp) -> Tuple[str, str]:
    """构建服务告警邮件的主题与正文。"""

    return _compose_message(
        ALERT_SUBJECT_TEMPLATE,
        "告警",
        "说明：监控检测到服务不可达",
        "发生时间",
        service_name,
        timestamp,
    )


def build_outage_recovery_message(service_name: str, timestamp) -> Tuple[str, str]:
    """构建服务恢复通知的主题与正文。"""

    return _compose_message(
        RECOVERY_SUBJECT_TEMPLATE,
        "恢复",
        "说明：监控检测到服务恢复至正常状态",
        "恢复时间",
        service_name,
        timestamp,
    )


def _compose_message(
    subject_prefix: str,
    status: str,
    detail_line: str,
    time_label: str,
    service_name: str,
    timestamp,
) -> Tuple[str, str]:
    subject = f"{subject_prefix} | {service_name}"
    body_lines = [
        f"状态：{status}",
        f"服务：{service_name}",
        detail_line,
        f"{time_label}：{timestamp}",
    ]
    return subject, "\n".join(body_lines)

def send_email(subject: str, body: str):
    # Get Mail info
    mailconfig = configuration.read_mail_configuration()
    smtp_server = mailconfig['smtp_server']
    smtp_port = mailconfig['smtp_port']
    username = mailconfig['username']
    password = mailconfig['password']
    from_addr = mailconfig['from_addr']
    to_addrs = mailconfig['to_addrs']

    # Create the message
    message = MIMEMultipart()
    message['From'] = from_addr
    message['To'] = to_addrs
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Attach file if specified
    # if attachment_file:
    #     with open(attachment_file, 'rb') as f:
    #         attachment = MIMEApplication(f.read(), _subtype='txt')
    #         attachment.add_header('Content-Disposition', 'attachment', filename=attachment_file)
    #         message.attach(attachment)

    # Connect to SMTP server and send message
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_addr, to_addrs.split(','), message.as_string())
    except smtplib.SMTPAuthenticationError as e:
        print("SMTP authentication error: ", e)
    except smtplib.SMTPException as e:
        print("SMTP error: ", e)
    except Exception as e:
        print("An error occurred: ", e)
