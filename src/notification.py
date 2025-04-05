import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from alert import ALERT_LEVELS_DISPLAY
import time


class Notification:
    def __init__(self, alert, image_path=None):
        self.alert = alert
        self.timestamp = time.time()
        self.image_path = image_path

    def __str__(self):
        return (
            f"Notification: {str(self.alert.message)} at {time.ctime(self.timestamp)}"
        )


class NotificationEngine:
    def __init__(self):
        load_dotenv()
        self.notify_emails = os.getenv("NOTIFY_EMAILS").split(",")
        self.sender_email = os.getenv("EMAIL_ADDRESS")
        self.send_pass = os.getenv("EMAIL_PASSWORD")
        self.notifications = []

    def add_notification(self, notification):
        self.notifications.append(notification)

    def send_notifications(self):
        for notification in self.notifications:
            print(str(notification))
            for email in self.notify_emails:
                self.send_email_notification(
                    to_email=email,
                    subject=f"Security Alert Level: {ALERT_LEVELS_DISPLAY[notification.alert.level]}",
                    body=str(notification),
                    image_path=notification.image_path,
                )
        self.notifications.clear()

    def send_email_notification(self, to_email, subject, body, image_path=None):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = to_email
        msg.set_content(body)

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img:
                img_data = img.read()
                msg.add_attachment(
                    img_data,
                    maintype="image",
                    subtype="jpeg",
                    filename=os.path.basename(image_path),
                )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(self.sender_email, self.send_pass)
            smtp.send_message(msg)
