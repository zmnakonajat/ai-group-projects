"""
Monitor Agent

PERCEIVES: RAM usage every 10 seconds
ACTS: Publishes RAM_DATA to the bus + updates taskbar icon
"""

import psutil
import time
import threading
from datetime import datetime
import pystray
from PIL import Image, ImageDraw
from core.base_agent import BaseAgent
from core.message_bus import MessageBus

# ============ CONFIGURATION ============
CHECK_INTERVAL = 10
RAM_THRESHOLD = 50

class MonitorAgent(BaseAgent):

    def __init__(self, bus: MessageBus):
        super().__init__("MonitorAgent", bus)
        self.tray_icon = None
        self.breach_start_time = None

    def run(self):
        print("=" * 50)
        print("MONITOR AGENT STARTED")
        print(f"Checking RAM every {CHECK_INTERVAL} seconds")
        print(f"Threshold: {RAM_THRESHOLD}%")
        print("=" * 50)

        self.setup_tray()

        while True:
            ram = self.get_ram_percent()
            processes = self.get_top_processes()

            # Update taskbar icon
            self.tray_icon.icon = self.create_icon_image(ram)
            self.tray_icon.title = f"RAM: {ram}%"

            # Print to terminal
            self.print_status(ram, processes)

            # Publish to bus so main.py receives it
            self.publish("RAM_DATA", {
                "ram_percent": ram,
                "top_processes": processes
            })

            time.sleep(CHECK_INTERVAL)

    def get_ram_percent(self):
        return psutil.virtual_memory().percent

    def get_top_processes(self):
        processes = []
        for proc in psutil.process_iter(['name', 'memory_percent']):
            try:
                processes.append({
                    'name': proc.info['name'],
                    'memory': round(proc.info['memory_percent'], 2)
                })
            except:
                pass
        processes.sort(key=lambda x: x['memory'], reverse=True)
        return processes[:3]

    def print_status(self, ram_percent, top_processes):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] RAM: {ram_percent}%")

        if ram_percent >= RAM_THRESHOLD:
            if self.breach_start_time is None:
                self.breach_start_time = time.time()
                print(f"⚠️  HIGH RAM! Started monitoring...")
            else:
                duration = int(time.time() - self.breach_start_time)
                print(f"⚠️  HIGH RAM for {duration} seconds!")
        else:
            if self.breach_start_time is not None:
                print("✓ RAM back to normal")
                self.breach_start_time = None
            else:
                print("✓ RAM normal")

        print(f"Top processes: ", end="")
        for i, proc in enumerate(top_processes):
            if i > 0:
                print(", ", end="")
            print(f"{proc['name']} ({proc['memory']}%)", end="")
        print()

    # ============ TASKBAR ICON ============
    def create_icon_image(self, ram_percent):
        image = Image.new('RGB', (256, 256), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)

        if ram_percent >= 50:
            color = (255, 0, 0)  # red - critical
        elif ram_percent >= 40:
            color = (255, 165, 0)  # orange - warning
        elif ram_percent >= 30:
            color = (255, 255, 0)  # yellow - moderate
        else:
            color = (0, 255, 0)  # green - normal

        draw.ellipse((4, 4, 252, 252), fill=color)
        return image

    def setup_tray(self):
        image = self.create_icon_image(0)
        self.tray_icon = pystray.Icon("RAM Monitor", image, "RAM: 0%")
        threading.Thread(target=self.tray_icon.run, daemon=True).start()


# ============ STANDALONE TEST ============
if __name__ == "__main__":
    from core.message_bus import MessageBus
    bus = MessageBus()
    agent = MonitorAgent(bus)
    agent.run()