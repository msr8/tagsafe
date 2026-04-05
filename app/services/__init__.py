from app.consts import MY_EMAIL, GMAIL_APP_PASSWORD, LLM_ENABLED, LLM_MODEL, OLLAMA_PORT

import requests as rq

import smtplib
from email.message import EmailMessage


def email(rec_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg.add_alternative(body, subtype='html')
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
    





def llm(prompt:str) -> str:
    if not LLM_ENABLED: return 'LLM is disabled'
    
    payload = {
        'model': LLM_MODEL,
        'prompt': prompt,
        'stream': False
    }

    resp = rq.post(f'http://localhost:{OLLAMA_PORT}/api/generate', json=payload)
    return resp.json()['response']