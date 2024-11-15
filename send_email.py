# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:56 p.m.
# @Author: weijiazhao
# @File : sendEmail.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configuration


def send_email(subject: str, body: str) -> None:
    """
    Send an email with the given subject and body.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.

    Returns:
        None
    """

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


def send_email_test(subject: str, mail_type: str) -> None:
    """
    Send an email to the recipients in the configuration file
    using the given subject and mail type.

    Args:
        subject (str): The subject of the email.
        mail_type (str): The type of the email. Supported types
        are 'Outage', 'Outage Resolution', 'Phase Incomplete',
        'Phase Incomplete Resolution'.

    Returns:
        None
    """

    # Get Mail info
    mailconfig = configuration.read_mail_configuration()
    smtp_server = mailconfig['smtp_server']
    smtp_port = mailconfig['smtp_port']
    username = mailconfig['username']
    password = mailconfig['password']
    from_addr = mailconfig['from_addr']
    to_addrs = mailconfig['to_addrs']

    if mail_type == 'Outage':
        body = data_outage_massage()
    elif mail_type == 'Outage Resolution':
        body = outage_resolution_massage()
    elif mail_type == 'Phase Incomplete':
        body = outage_resolution_massage()
    elif mail_type == 'Phase Incomplete Resolution':
        body = outage_resolution_massage()

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
    return mail_content


def outage_resolution_massage(mail_type: str):
    mail_content = configuration.get_mail_formate('Outage_Resolution')
    return mail_content


def phase_incomplete(mail_type: str):
    mail_content = configuration.get_mail_formate('Phase_Incomplete')
    return mail_content


def phase_incomplete_resolution(mail_type: str):
    mail_content = configuration.get_mail_formate(
        'Phase_Incomplete_Resolution')
    return mail_content


# send_email_test("Test", 'Outage Resolution')
