import smtplib
import os
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(to_email, otp, purpose="verification"):
    from_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    if not from_email or not password:
        raise ValueError("EMAIL_ADDRESS or EMAIL_PASSWORD missing from Render variables!")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email

    if purpose == "reset":
        msg['Subject'] = "Password Reset - AI Research Portal"
        body = f"""
        <div style="font-family: Arial; max-width: 400px; margin: auto; padding: 30px; border-radius: 10px; background: #f8fafc;">
        <h2 style="color: #2563eb;">Password Reset Request</h2>
        <p>Your password reset OTP is:</p>
        <h1 style="color: #2563eb; letter-spacing: 8px; font-size: 40px;">{otp}</h1>
        <p>This code expires in 10 minutes.</p>
        <p style="color: #999;">If you did not request this, ignore this email.</p>
        </div>
        """
    else:
        msg['Subject'] = "Verify Your Email - AI Research Portal"
        body = f"""
        <div style="font-family: Arial; max-width: 400px; margin: auto; padding: 30px; border-radius: 10px; background: #f8fafc;">
        <h2 style="color: #2563eb;">Welcome to AI Research Portal!</h2>
        <p>Your email verification OTP is:</p>
        <h1 style="color: #2563eb; letter-spacing: 8px; font-size: 40px;">{otp}</h1>
        <p>Enter this code to activate your account.</p>
        </div>
        """

    msg.attach(MIMEText(body, 'html'))

    # timeout=10 prevents the website from hanging forever!
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
        server.login(from_email, password)
        server.send_message(msg)