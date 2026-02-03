import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv, find_dotenv


# This finds the .env file and loads the variables
load_dotenv(find_dotenv())

def send_email():
    # Fetch credentials from environment variables  
    EMAIL_ADDRESS = os.environ.get('EMAIL_USER')    
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    RECIPIENT = os.environ.get('EMAIL_RECEIVER')

    msg = EmailMessage()
    msg['Subject'] = 'Daily Signals settig positions'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT
    msg.set_content('Here should be the table with the signals.')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully.")

if __name__ == "__main__":
    send_email()


#print(EMAIL_ADDRESS)
