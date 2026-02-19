import threading
from abc import ABC, abstractmethod
from core.message_bus import MessageBus
from core.message import Message


class BaseAgent(ABC):
    def __init__(self, name, bus):
        self.name = name
        self.bus = bus
        self._thread = threading.Thread(
            target=self._run_safe,
            name=name,
            daemon=True
        )

    def publish(self, event_type, payload):
        msg = Message(
            event_type=event_type,
            payload=payload,
            sender=self.name
        )
        self.bus.publish(msg)

    def start(self):
        print(f"[{self.name}] Starting...")
        self._thread.start()

    def _run_safe(self):
        try:
            self.run()
        except Exception as e:
            print(f"[{self.name}] CRASHED: {e}")

    @abstractmethod
    def run(self):
        pass