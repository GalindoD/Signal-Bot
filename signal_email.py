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

    # 2. Fallback: If variables aren't set, ask for them manually (Local testing)
    if not email_user or not email_pass:
        print("--- Local Execution Detected ---")
        email_user = email_user or input("Enter your Gmail address: ")
        email_pass = email_pass or input("Enter your 16-character App Password: ")
        email_receiver = email_receiver or email_user  # Default to sending to yourself

    msg = EmailMessage()
    msg['Subject'] = 'Daily Automated Update'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT
    msg.set_content('Hello! This is your automated daily email sent via GitHub Actions.')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully.")

if __name__ == "__main__":
    send_email()


print(EMAIL_ADDRESS)
