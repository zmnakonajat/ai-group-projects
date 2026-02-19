"""
Email Agent

PERCEIVES: SEND_EMAIL messages from the bus
ACTS: Sends email alert
"""

import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from core.base_agent import BaseAgent
from core.message_bus import MessageBus

load_dotenv()


class EmailAgent(BaseAgent):

    def __init__(self, bus: MessageBus):
        super().__init__("EmailAgent", bus)
        self.bus.subscribe("SEND_EMAIL", self.on_send_email)

        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender = os.getenv("SENDER_EMAIL")
        self.password = os.getenv("SENDER_PASSWORD")
        self.recipient = os.getenv("RECIPIENT_EMAIL")

    def run(self):
        print(f"[{self.name}] Ready. Waiting for events...")
        while True:
            time.sleep(1)

    def on_send_email(self, message):
        ram = message.payload["ram_percent"]
        processes = message.payload["top_processes"]
        print(f"[{self.name}] 📧 Received SEND_EMAIL — sending email!")
        self.send_email(ram, processes)

    def send_email(self, ram_percent, top_processes):
        if not self.sender or not self.password:
            print(f"[{self.name}] ✗ Email credentials not found in .env file!")
            return

        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = f"⚠️ HIGH RAM ALERT: {ram_percent}%"

        body = f"""
HIGH RAM USAGE DETECTED!

Current RAM Usage: {ram_percent}%

Top RAM-Consuming Processes:
"""
        for i, proc in enumerate(top_processes, 1):
            body += f"  {i}. {proc['name']}: {proc['memory']}%\n"

        body += """
Please check the system and close unnecessary programs.

---
This is an automated alert from RAM Monitor System
"""
        msg.attach(MIMEText(body, 'plain'))

        try:
            print(f"[{self.name}] 📧 Sending email to {self.recipient}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
            print(f"[{self.name}] ✓ Email sent successfully!")
        except Exception as e:
            print(f"[{self.name}] ✗ Email failed: {e}")


# ============ STANDALONE TEST ============
if __name__ == "__main__":
    from core.message_bus import MessageBus
    import threading
    bus = MessageBus()
    agent = EmailAgent(bus)
    threading.Thread(target=bus.start_routing, daemon=True).start()
    agent.run()