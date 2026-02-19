import queue
import threading

class MessageBus:
    def __init__(self):
        self._queue = queue.Queue()
        self._subscribers = {}
        self._lock = threading.Lock()
        self._running = False


    def subscribe(self, event_type, callback):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def publish(self, message):
        self._queue.put(message)


    def start_routing(self):
        self._running = True
        while self._running:
            try:
                message = self._queue.get(timeout=1.0)
                self._route(message)
            except queue.Empty:
                continue


    def _route(self, message):
        with self._lock:
            subscribers = self._subscribers.get(message.event_type, [])

        for callback in subscribers:
            threading.Thread(target=callback, args=(message,), daemon=True).start()

    def stop(self):
        self._running = False