#!/usr/bin/env python3
"""
Send failure notification email for Jenkins pipeline
"""

import sys
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_failure_email(smtp_server, smtp_port, smtp_user, smtp_pass, recipients, job_name, build_number, build_url):
    """Send a failure notification email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipients
        msg['Subject'] = 'Jenkins OSS Upload Pipeline Failed'
        
        body = f"""
Jenkins Pipeline Failure Report

Job: {job_name}
Build Number: {build_number}
Build URL: {build_url}

The static resource upload pipeline has failed. Please check the Jenkins console output for details.
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        print('Failure notification email sent successfully')
        return True
    except Exception as e:
        print(f'Failed to send email notification: {e}')
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send failure notification email')
    parser.add_argument('--smtp-server', required=True)
    parser.add_argument('--smtp-port', required=True)
    parser.add_argument('--smtp-username', required=True)
    parser.add_argument('--smtp-password', required=True)
    parser.add_argument('--recipients', required=True)
    parser.add_argument('--job-name', required=True)
    parser.add_argument('--build-number', required=True)
    parser.add_argument('--build-url', required=True)
    
    args = parser.parse_args()
    
    success = send_failure_email(
        args.smtp_server,
        args.smtp_port,
        args.smtp_username,
        args.smtp_password,
        args.recipients,
        args.job_name,
        args.build_number,
        args.build_url
    )
    
    sys.exit(0 if success else 1)
