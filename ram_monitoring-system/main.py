import threading
import time
import os
from core.message_bus import MessageBus
from core.message import Message
from agents.monitor_agent import MonitorAgent
from agents.alert_agent import AlertAgent
from agents.email_agent import EmailAgent
from agents.dashboard_agent import DashboardAgent
from agents.logger_agent import LoggerAgent
from agents.recovery_agent import RestartAgent

ram_high_since = None
email_sent = False
restart_triggered = False


def on_ram_data(message):
    global ram_high_since, email_sent, restart_triggered
    ram = message.payload['ram_percent']
    processes = message.payload['top_processes']


    if ram >= 50:
        if ram_high_since is None:
            ram_high_since = time.time()
            email_sent = False
            restart_triggered = False
            bus.publish(Message(
                event_type="RAM_HIGH",
                payload={"ram_percent": ram, "top_processes": processes},
                sender="main"
            ))

        duration = time.time() - ram_high_since

        if duration >= 20 and not email_sent:
            email_sent = True
            bus.publish(Message(
                event_type="SEND_EMAIL",
                payload={"ram_percent": ram, "top_processes": processes},
                sender="main"
            ))

        if duration >= 30 and not restart_triggered:
            restart_triggered = True
            bus.publish(Message(
                event_type="RESTART",
                payload={"ram_percent": ram, "top_processes": processes},
                sender="main"
            ))
    else:
        if ram_high_since is not None:
            ram_high_since = None
            email_sent = False
            restart_triggered = False
            bus.publish(Message(
                event_type="RAM_NORMAL",
                payload={"ram_percent": ram, "top_processes": processes},
                sender="main"
            ))


def main():
    print("=" * 55)
    print("   RAM MONITORING SYSTEM")
    print("=" * 55)

    global bus
    bus = MessageBus()

    bus.subscribe("RAM_DATA", on_ram_data)

    agents = [
        MonitorAgent(bus),
        AlertAgent(bus),
        EmailAgent(bus),
        DashboardAgent(bus),
        LoggerAgent(bus),
        RestartAgent(bus),

    ]

    threading.Thread(target=bus.start_routing, name="MessageBus", daemon=True).start()

    for agent in agents:
        agent.start()

    print("\n[MAIN] All agents running. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        bus.stop()
        print("\n[MAIN] System stopped.")
        import os
        os._exit(0)


if __name__ == "__main__":
    main()
