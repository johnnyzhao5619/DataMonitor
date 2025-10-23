# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:56 p.m.
# @Author: weijiazhao
# @File : send_email.py
# @Software: PyCharm

import datetime as _dt
import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from typing import Iterable, Mapping, Optional, Tuple

try:
    from PyQt5 import QtCore
except ModuleNotFoundError:  # pragma: no cover - 提供兼容性
    class _FallbackCoreApplication:
        @staticmethod
        def translate(_context: str, text: str) -> str:
            return text

    class _FallbackQtCore:
        QCoreApplication = _FallbackCoreApplication

    QtCore = _FallbackQtCore()  # type: ignore[assignment]

import configuration


LOGGER = logging.getLogger(__name__)


def _translate(text: str) -> str:
    return QtCore.QCoreApplication.translate("Email", text)


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


def render_email(
    event: str, context: Mapping[str, object], *, language: Optional[str] = None
) -> Tuple[str, str]:
    """根据事件类型渲染邮件主题与正文。"""

    if event not in MAIL_EVENT_MAP:
        raise KeyError(_translate("未知的邮件事件类型：{event}").format(event=event))

    missing_fields = [field for field in REQUIRED_CONTEXT_FIELDS if field not in context]
    if missing_fields:
        raise ValueError(
            _translate("邮件模版缺少必要字段：{fields}").format(
                fields=", ".join(sorted(missing_fields))
            )
        )

    mapping = MAIL_EVENT_MAP[event]
    subject = configuration.render_template(
        "mail", mapping["subject"], context, language=language
    )
    body = configuration.render_template(
        "mail", mapping["body"], context, language=language
    )
    return subject, body


def _normalise_timestamp(occurred_at) -> str:
    if isinstance(occurred_at, str):
        return occurred_at
    if isinstance(occurred_at, (_dt.datetime, _dt.date)):
        return occurred_at.strftime("%Y-%m-%d %H:%M:%S")
    return str(occurred_at)


def _build_notification(
    event: str, service_name, occurred_at, language: Optional[str] = None
) -> Tuple[str, str]:
    context_defaults = _event_context_presets(event)

    context = {
        "service_name": str(service_name) if service_name is not None else "",
        "event_timestamp": _normalise_timestamp(occurred_at),
        **context_defaults,
    }
    return render_email(event, context, language=language)


def build_outage_alert_message(
    service_name, occurred_at, language: Optional[str] = None
) -> Tuple[str, str]:
    return _build_notification("alert", service_name, occurred_at, language)


def build_outage_recovery_message(
    service_name, occurred_at, language: Optional[str] = None
) -> Tuple[str, str]:
    return _build_notification("recovery", service_name, occurred_at, language)


def _normalize_recipients(
    explicit_recipients,
    default_recipients: str,
) -> Tuple[str, Iterable[str]]:
    """返回用于邮件头和发送列表的收件人信息。"""

    candidate = explicit_recipients if explicit_recipients else default_recipients
    if candidate is None:
        raise ValueError(_translate("未配置任何收件人地址"))

    if isinstance(candidate, str):
        addresses = [addr.strip() for addr in candidate.split(",") if addr.strip()]
    else:
        try:
            iterator = iter(candidate)
        except TypeError as exc:  # pragma: no cover - defensive programming
            raise TypeError(_translate("收件人必须为字符串或可迭代对象")) from exc
        addresses = [str(addr).strip() for addr in iterator if str(addr).strip()]

    if not addresses:
        raise ValueError(_translate("收件人地址不能为空"))

    return ", ".join(addresses), addresses


def _format_address(address: str) -> str:
    """将地址字符串转换为符合 RFC 的显示格式，并保证 UTF-8 编码。"""

    name, email_addr = parseaddr(address)
    if not email_addr:
        if name:
            return str(Header(name, "utf-8"))
        return str(Header(address, "utf-8"))

    if name:
        return formataddr((str(Header(name, "utf-8")), email_addr))
    return email_addr


def _extract_email(address: str) -> str:
    """从地址字符串中提取用于 SMTP 传输的邮箱地址。"""

    return parseaddr(address)[1] or address


def send_email(subject: str, body: str, recipients=None):
    # Get Mail info
    mailconfig = configuration.read_mail_configuration()
    smtp_server = mailconfig['smtp_server']
    try:
        smtp_port = int(mailconfig['smtp_port'])
    except (TypeError, ValueError) as exc:
        raise ValueError(_translate("SMTP 端口配置必须为整数")) from exc
    username = mailconfig['username']
    password = mailconfig['password']
    from_addr = mailconfig['from_addr']
    to_addrs = mailconfig['to_addrs']
    use_starttls = mailconfig.get('use_starttls', False)
    use_ssl = mailconfig.get('use_ssl', False)

    if use_starttls and use_ssl:
        raise ValueError(_translate("邮件配置 use_starttls 与 use_ssl 不能同时启用"))

    _, send_to_list = _normalize_recipients(recipients, to_addrs)
    display_from = _format_address(from_addr)
    display_to = ", ".join(_format_address(addr) for addr in send_to_list)
    transmit_from = _extract_email(from_addr)
    transmit_to = [_extract_email(addr) for addr in send_to_list]

    # Create the message
    message = MIMEMultipart()
    message['From'] = display_from
    message['To'] = display_to
    message['Subject'] = Header(subject, 'utf-8')
    message.attach(MIMEText(body, 'plain', 'utf-8'))

    # Attach file if specified
    # if attachment_file:
    #     with open(attachment_file, 'rb') as f:
    #         attachment = MIMEApplication(f.read(), _subtype='txt')
    #         attachment.add_header('Content-Disposition', 'attachment', filename=attachment_file)
    #         message.attach(attachment)

    # Connect to SMTP server and send message
    smtp_factory = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP

    try:
        with smtp_factory(smtp_server, smtp_port) as server:
            if use_starttls:
                server.starttls()
            server.login(username, password)
            server.sendmail(transmit_from, transmit_to, message.as_string())
    except smtplib.SMTPAuthenticationError:
        message = _translate("SMTP 身份验证失败：")
        LOGGER.exception(
            "mail.smtp.authentication_error message=%s server=%s username=%s recipients=%s",
            message,
            smtp_server,
            username,
            display_to,
        )
        raise
    except smtplib.SMTPException:
        message = _translate("SMTP 通信异常：")
        LOGGER.exception(
            "mail.smtp.communication_error message=%s server=%s port=%s recipients=%s",
            message,
            smtp_server,
            smtp_port,
            display_to,
        )
        raise
    except Exception:
        message = _translate("发生未知错误：")
        LOGGER.exception(
            "mail.smtp.unknown_error message=%s server=%s port=%s recipients=%s",
            message,
            smtp_server,
            smtp_port,
            display_to,
        )
        raise


def _event_context_presets(event: str) -> Mapping[str, str]:
    if event == "alert":
        return {
            "status_action": _translate("告警"),
            "event_description": _translate("监控检测到服务不可达"),
            "time_label": _translate("发生时间"),
        }
    if event == "recovery":
        return {
            "status_action": _translate("恢复"),
            "event_description": _translate("监控检测到服务恢复至正常状态"),
            "time_label": _translate("恢复时间"),
        }
    raise KeyError(_translate("未知的邮件事件类型：{event}").format(event=event))

