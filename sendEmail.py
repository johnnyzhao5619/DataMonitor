# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:56 p.m.
# @Author: weijiazhao
# @File : sendEmail.py
# @Software: PyCharm

import datetime as _dt
import contextlib
import importlib.util
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Mapping, Tuple

import configuration
import sys


def _load_qtcore():  # pragma: no cover - environment dependent
    with contextlib.suppress(ValueError, ModuleNotFoundError):
        if importlib.util.find_spec("PyQt5") is not None:
            from PyQt5 import QtCore  # type: ignore
            return QtCore
    module = sys.modules.get("PyQt5")
    if module is not None:
        qt_core = getattr(module, "QtCore", None)
        if qt_core is not None:
            return qt_core

    class _QtCoreFallback:  # pylint: disable=too-few-public-methods
        class QCoreApplication:  # pylint: disable=too-few-public-methods
            @staticmethod
            def translate(_context: str, text: str) -> str:
                return text

    return _QtCoreFallback()  # type: ignore


QtCore = _load_qtcore()


def _tr(text: str) -> str:
    return QtCore.QCoreApplication.translate("sendEmail", text)


MAIL_EVENT_MAP = {
    "alert": {"subject": "alert_subject", "body": "alert_body"},
    "recovery": {"subject": "recovery_subject", "body": "recovery_body"},
}

_EVENT_CONTEXT_PRESETS = {
    "alert": {
        "status_action": "告警",
        "event_description": "监控检测到服务不可达",
        "time_label": "发生时间",
    },
    "recovery": {
        "status_action": "恢复",
        "event_description": "监控检测到服务恢复至正常状态",
        "time_label": "恢复时间",
    },
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
        raise KeyError(_tr("未知的邮件事件类型：{event}").format(event=event))

    missing_fields = [field for field in REQUIRED_CONTEXT_FIELDS if field not in context]
    if missing_fields:
        raise ValueError(
            _tr("邮件模版缺少必要字段：{fields}").format(
                fields=", ".join(sorted(missing_fields))
            )
        )

    mapping = MAIL_EVENT_MAP[event]
    subject = configuration.render_template("mail", mapping["subject"], context)
    body = configuration.render_template("mail", mapping["body"], context)
    return subject, body


def _normalise_timestamp(occurred_at) -> str:
    if isinstance(occurred_at, str):
        return occurred_at
    if isinstance(occurred_at, (_dt.datetime, _dt.date)):
        return occurred_at.strftime("%Y-%m-%d %H:%M:%S")
    return str(occurred_at)


def _build_notification(event: str, service_name, occurred_at) -> Tuple[str, str]:
    try:
        context_defaults = {
            key: _tr(value) for key, value in _EVENT_CONTEXT_PRESETS[event].items()
        }
    except KeyError as exc:
        raise KeyError(_tr("未知的邮件事件类型：{event}").format(event=event)) from exc

    context = {
        "service_name": str(service_name) if service_name is not None else "",
        "event_timestamp": _normalise_timestamp(occurred_at),
        **context_defaults,
    }
    return render_email(event, context)


def build_outage_alert_message(service_name, occurred_at) -> Tuple[str, str]:
    return _build_notification("alert", service_name, occurred_at)


def build_outage_recovery_message(service_name, occurred_at) -> Tuple[str, str]:
    return _build_notification("recovery", service_name, occurred_at)


def _normalize_recipients(
    explicit_recipients,
    default_recipients: str,
) -> Tuple[str, Iterable[str]]:
    """返回用于邮件头和发送列表的收件人信息。"""

    candidate = explicit_recipients if explicit_recipients else default_recipients
    if candidate is None:
        raise ValueError(_tr("未配置任何收件人地址"))

    if isinstance(candidate, str):
        addresses = [addr.strip() for addr in candidate.split(",") if addr.strip()]
    else:
        try:
            iterator = iter(candidate)
        except TypeError as exc:  # pragma: no cover - defensive programming
            raise TypeError(_tr("收件人必须为字符串或可迭代对象")) from exc
        addresses = [str(addr).strip() for addr in iterator if str(addr).strip()]

    if not addresses:
        raise ValueError(_tr("收件人地址不能为空"))

    return ", ".join(addresses), addresses


def send_email(subject: str, body: str, recipients=None):
    # Get Mail info
    mailconfig = configuration.read_mail_configuration()
    smtp_server = mailconfig['smtp_server']
    try:
        smtp_port = int(mailconfig['smtp_port'])
    except (TypeError, ValueError) as exc:
        raise ValueError(_tr("SMTP 端口配置必须为整数")) from exc
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
    except smtplib.SMTPAuthenticationError as error:
        print(_tr("SMTP 身份验证失败：{error}").format(error=error))
    except smtplib.SMTPException as error:
        print(_tr("SMTP 错误：{error}").format(error=error))
    except Exception as error:
        print(_tr("发送邮件时出现异常：{error}").format(error=error))
