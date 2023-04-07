# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:56 p.m.
# @Author: weijiazhao
# @File : sendEmail.py
# @Software: PyCharm

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configuration

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
