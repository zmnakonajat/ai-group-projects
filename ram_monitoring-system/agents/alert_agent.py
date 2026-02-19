"""
Alert Agent

PERCEIVES: RAM_HIGH / RAM_NORMAL messages from the bus
ACTS: Shows popup + plays sound
"""

import time
import threading
from core.base_agent import BaseAgent
from core.message_bus import MessageBus


class AlertAgent(BaseAgent):

    def __init__(self, bus: MessageBus):
        super().__init__("AlertAgent", bus)
        self.bus.subscribe("RAM_HIGH", self.on_ram_high)
        self.bus.subscribe("RAM_NORMAL", self.on_ram_normal)

    def run(self):
        print(f"[{self.name}] Ready. Waiting for events...")
        while True:
            time.sleep(1)

    def on_ram_high(self, message):
        ram = message.payload["ram_percent"]
        processes = message.payload["top_processes"]
        print(f"[{self.name}] ⚠ RAM HIGH ({ram}%) — showing alert!")
        self.play_sound()
        self.show_popup(ram, processes)

    def on_ram_normal(self, message):
        ram = message.payload["ram_percent"]
        print(f"[{self.name}] ✓ RAM normal ({ram}%) — alert cleared")

    def show_popup(self, ram, processes):
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            message = f"⚠️  HIGH RAM USAGE DETECTED! ⚠️\n\n"
            message += f"RAM Usage: {ram}%\n\n"
            message += "Top processes:\n"
            for i, proc in enumerate(processes, 1):
                message += f"  {i}. {proc['name']}: {proc['memory']}%\n"
            message += "\nPlease close some programs!"
            messagebox.showwarning("RAM Alert", message)
            root.destroy()
        except Exception as e:
            print(f"[{self.name}] Popup failed: {e}")

    def play_sound(self):
        try:
            import winsound
            winsound.Beep(1000, 500)
        except:
            print(f"[{self.name}] 🔊 alert sound")


# ============ STANDALONE TEST ============
if __name__ == "__main__":
    from core.message_bus import MessageBus
    bus = MessageBus()
    agent = AlertAgent(bus)
    threading.Thread(target=bus.start_routing, daemon=True).start()
    agent.run()