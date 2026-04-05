from app.consts import GMAIL_APP_PASSWORD, MY_EMAIL

import smtplib
from email.message import EmailMessage


def email(rec_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From']    = MY_EMAIL
    msg['To']      = rec_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            # Log in to your account
            server.login(msg['From'], GMAIL_APP_PASSWORD)
            # Send the email
            server.send_message(msg)
            
        print("Email sent successfully! 🚀")

    except Exception as e:
        print(f"Failed to send email. Error: {e}")