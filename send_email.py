# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:56 p.m.
# @Author: weijiazhao
# @File : send_email.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

import configuration


def format_event_email(event: str, service_name: str, timestamp,
                       remark: str) -> (str, str):
    """
    Build subject/body from configurable templates with fallbacks.
    """
    ts = timestamp if isinstance(timestamp, str) else str(timestamp)
    defaults = {
        'outage': {
            'subject': f"{ts}: The {service_name} server outage!",
            'body': f"{service_name} Outage\nTime: {ts}\nRemark: {remark}"
        },
        'restored': {
            'subject':
            f"{ts}: The {service_name} service were restored!",
            'body':
            f"{service_name} Service Restored\nRestored Time: {ts}\nRemark: {remark}"
        }
    }
    template_keys = {
        'outage': ('outage_subject', 'outage_body'),
        'restored': ('restored_subject', 'restored_body'),
    }
    key_pair = template_keys.get(event, ('', ''))
    subject_tpl = configuration.get_template(
        key_pair[0],
        defaults.get(event, {}).get('subject', ''))
    body_tpl = configuration.get_template(
        key_pair[1],
        defaults.get(event, {}).get('body', ''))
    context = {
        'service_name': service_name,
        'timestamp': ts,
        'remark': remark,
    }
    try:
        subject = subject_tpl.format(**context)
        body = body_tpl.format(**context)
    except Exception:
        subject = defaults.get(event, {}).get('subject', '')
        body = defaults.get(event, {}).get('body', '')
    return subject, body


def send_email(subject: str, body: str, to_addrs: str) -> None:
    """
    Send an email with the given subject and body.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_addrs (str): The comma-separated list of recipients.

    Returns:
        None
    """

    # Get Mail info
    mailconfig = configuration.read_mail_configuration()
    smtp_server: str = mailconfig['smtp_server']
    smtp_port: int = int(mailconfig['smtp_port'])
    username: str = mailconfig['username']
    password: str = mailconfig['password']
    from_addr: str = mailconfig['from_addr']

    if not smtp_server or not username or not password:
        print("SMTP configuration incomplete, skip sending email.")
        return
    if not to_addrs:
        print("No recipients provided, skip sending email.")
        return

    # Create the message
    message = MIMEMultipart()
    message['From'] = from_addr
    message['To'] = to_addrs
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_addr, to_addrs.split(','),
                            message.as_string())
    except smtplib.SMTPAuthenticationError as e:
        print("SMTP authentication error: ", e)
    except smtplib.SMTPException as e:
        print("SMTP error: ", e)
    except Exception as e:
        print("An error occurred: ", e)


def send_email_test(subject: str, mail_type: str, to_addrs: str) -> None:
    """
    Send an email to the recipients using the given subject and mail type.

    Args:
        subject (str): The subject of the email.
        mail_type (str): The type of the email. Supported types
                         are 'Outage', 'Outage Resolution', 'Phase Incomplete',
                         'Phase Incomplete Resolution'.
        to_addrs (str): The comma-separated list of recipients.

    Returns:
        None
    """

    # Get Mail info
    mailconfig: Dict[str, str] = configuration.read_mail_configuration()
    smtp_server: str = mailconfig['smtp_server']
    smtp_port: int = int(mailconfig['smtp_port'])
    username: str = mailconfig['username']
    password: str = mailconfig['password']
    from_addr: str = mailconfig['from_addr']

    if not smtp_server or not username or not password:
        print("SMTP configuration incomplete, skip sending test email.")
        return
    if not to_addrs:
        print("No recipients provided, skip sending test email.")
        return

    body: str
    if mail_type == 'Outage':
        body = data_outage_massage(mail_type)
    elif mail_type == 'Outage Resolution':
        body = outage_resolution_massage(mail_type)
    elif mail_type == 'Phase Incomplete':
        body = phase_incomplete(mail_type)
    elif mail_type == 'Phase Incomplete Resolution':
        body = phase_incomplete_resolution(mail_type)
    else:
        raise ValueError("Unsupported mail type")

    # Create the message
    message = MIMEMultipart()
    message['From'] = from_addr
    message['To'] = to_addrs
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_addr, to_addrs.split(','),
                            message.as_string())
    except smtplib.SMTPAuthenticationError as e:
        print("SMTP authentication error: ", e)
    except smtplib.SMTPException as e:
        print("SMTP error: ", e)
    except Exception as e:
        print("An error occurred: ", e)


def data_outage_massage(mail_type: str):
    mail_content = configuration.get_mail_formate('Outage')
    return mail_content or f"{mail_type} notification"


def outage_resolution_massage(mail_type: str):
    mail_content = configuration.get_mail_formate('Outage_Resolution')
    return mail_content or f"{mail_type} notification"


def phase_incomplete(mail_type: str):
    mail_content = configuration.get_mail_formate('Phase_Incomplete')
    return mail_content or f"{mail_type} notification"


def phase_incomplete_resolution(mail_type: str):
    mail_content = configuration.get_mail_formate(
        'Phase_Incomplete_Resolution')
    return mail_content or f"{mail_type} notification"


# send_email_test("Test", 'Outage Resolution')
