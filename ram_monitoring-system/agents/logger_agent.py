import psutil
import csv
import time
import threading
from datetime import datetime
import os
from core.base_agent import BaseAgent
from core.message_bus import MessageBus


THRESHOLD = 80
LOG_FILE = "ram_log.csv"

class LoggerAgent(BaseAgent):
    def __init__(self, bus:MessageBus):
        super().__init__("LoggerAgent",bus)
        self.log_file = "ram_log.csv"
        self.latest_ram = 0
        self.bus.subscribe("RAM_HIGH",self.on_ram_high)
        self.bus.subscribe("RAM_NORMAL",self.on_ram_normal)
        self.bus.subscribe("SEND_EMAIL", self.on_email_sent)
        self.bus.subscribe("RESTART",self.on_restart)
        self.bus.subscribe("RAM_DATA",self.on_ram_data)
    def run(self):
        print(f"[{self.name}] Ready. Logging to {self.log_file}")
        self._setup_csv()
        threading.Thread(target=self._snapshot_loop, daemon=True).start()
        while True:
            time.sleep(1);

    def _setup_csv(self):
        if not os.path.isfile(self.log_file):
            with open(self.log_file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp","Event","RAM%","Details"])
    def _write_log(self,event,ram,details):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp,event,f"{ram}%",details])
            print(f"[{self.name}] Logged: {event} | {ram}% | {details}")

    def on_ram_high(self, message):
        ram = message.payload["ram_percent"]
        self._write_log("RAM_HIGH", ram, "Threshold breached")

    def on_ram_normal(self, message):
        ram = message.payload["ram_percent"]
        self._write_log("RAM_NORMAL", ram, "RAM back to normal")

    def on_email_sent(self, message):
        ram = message.payload["ram_percent"]
        self._write_log("EMAIL_SENT", ram, "Alert email sent")

    def on_restart(self, message):
        ram = message.payload["ram_percent"]
        self._write_log("RESTART", ram, "System restart triggered")

    def on_ram_data(self, message):
        self.latest_ram = message.payload["ram_percent"]

    def _snapshot_loop(self):
        while True:
            time.sleep(6 * 60 * 60)  # 6 hours in seconds
            self._write_log("SNAPSHOT", self.latest_ram, "Scheduled 6-hour report")

# ============ STANDALONE TEST ============
if __name__ == "__main__":
    from core.message_bus import MessageBus
    bus = MessageBus()
    agent = LoggerAgent(bus)
    threading.Thread(target=bus.start_routing, daemon=True).start()
    agent.run()

