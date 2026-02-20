"""
Restart Agent

PERCEIVES: RESTART messages from the bus
ACTS: Restarts the system
"""

import os
import time
import threading
from core.base_agent import BaseAgent
from core.message_bus import MessageBus


class RestartAgent(BaseAgent):

    def __init__(self, bus: MessageBus):
        super().__init__("RestartAgent", bus)
        self.bus.subscribe("RESTART", self.on_restart)

    def run(self):
        print(f"[{self.name}] Ready. Waiting for events...")
        while True:
            time.sleep(1)

    def on_restart(self, message):
        ram = message.payload["ram_percent"]
        print(f"[{self.name}] ⚠️ RAM critically high ({ram}%) — restarting in 10 seconds!")
        print(f"[{self.name}] Press Ctrl+C to cancel!")
        time.sleep(10)
        print(f"[{self.name}] Restarting now...")
        os.system("shutdown /r /t 0")