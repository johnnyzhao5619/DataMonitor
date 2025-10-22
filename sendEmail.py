# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:56 p.m.
# @Author: weijiazhao
# @File : sendEmail.py
# @Software: PyCharm

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Mapping, Tuple

import configuration


MAIL_EVENT_MAP = {
    "alert": {"subject": "alert_subject", "body": "alert_body"},
    "recovery": {"subject": "recovery_subject", "body": "recovery_body"},
}

REQUIRED_CONTEXT_FIELDS = {
    "service_name",
    "event_timestamp",
    "status_action",
    "event_description",
    "time_label",
}


def render_email(event: str, context: Mapping[str, object]) -> Tuple[str, str]:
    """根据事件类型渲染邮件主题与正文。"""

    if event not in MAIL_EVENT_MAP:
        raise KeyError(f"未知的邮件事件类型：{event}")

    missing_fields = [field for field in REQUIRED_CONTEXT_FIELDS if field not in context]
    if missing_fields:
        raise ValueError(
            "邮件模版缺少必要字段：{}".format(", ".join(sorted(missing_fields)))
        )

    mapping = MAIL_EVENT_MAP[event]
    subject = configuration.render_template("mail", mapping["subject"], context)
    body = configuration.render_template("mail", mapping["body"], context)
    return subject, body

def _normalize_recipients(
    explicit_recipients,
    default_recipients: str,
) -> Tuple[str, Iterable[str]]:
    """返回用于邮件头和发送列表的收件人信息。"""

    candidate = explicit_recipients if explicit_recipients else default_recipients
    if candidate is None:
        raise ValueError("未配置任何收件人地址")

    if isinstance(candidate, str):
        addresses = [addr.strip() for addr in candidate.split(",") if addr.strip()]
    else:
        try:
            iterator = iter(candidate)
        except TypeError as exc:  # pragma: no cover - defensive programming
            raise TypeError("收件人必须为字符串或可迭代对象") from exc
        addresses = [str(addr).strip() for addr in iterator if str(addr).strip()]

    if not addresses:
        raise ValueError("收件人地址不能为空")

    return ", ".join(addresses), addresses


def send_email(subject: str, body: str, recipients=None):
    # Get Mail info
    mailconfig = configuration.read_mail_configuration()
    smtp_server = mailconfig['smtp_server']
    try:
        smtp_port = int(mailconfig['smtp_port'])
    except (TypeError, ValueError) as exc:
        raise ValueError("SMTP 端口配置必须为整数") from exc
    username = mailconfig['username']
    password = mailconfig['password']
    from_addr = mailconfig['from_addr']
    to_addrs = mailconfig['to_addrs']

    header_to, send_to_list = _normalize_recipients(recipients, to_addrs)

    # Create the message
    message = MIMEMultipart()
    message['From'] = from_addr
    message['To'] = header_to
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
            server.sendmail(from_addr, list(send_to_list), message.as_string())
    except smtplib.SMTPAuthenticationError as e:
        print("SMTP authentication error: ", e)
    except smtplib.SMTPException as e:
        print("SMTP error: ", e)
    except Exception as e:
        print("An error occurred: ", e)
