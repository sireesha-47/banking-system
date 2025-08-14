import smtplib
from config import Config

def send_otp_email(receiver_email, otp):
    sender_email = Config.MAIL_SENDER
    sender_password = Config.MAIL_PASSWORD
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"
    message = f"Subject: {subject}\n\n{body}"

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
        print(f"✅ OTP sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
