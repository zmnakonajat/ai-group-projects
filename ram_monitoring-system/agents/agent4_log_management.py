import psutil
import csv
import time
from datetime import datetime
import os

THRESHOLD = 80
LOG_FILE = "ram_log.csv"

def log_ram_usage():
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Timestamp", "RAM Usage (%)", "Status"])

        try:
            while True:
                ram = psutil.virtual_memory()
                usage = ram.percent
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                status = "CRITICAL" if usage > THRESHOLD else "Normal"

                writer.writerow([timestamp, usage, status])
                file.flush()

                print(f"{timestamp} | RAM: {usage}% | {status}")
                time.sleep(5)

        except KeyboardInterrupt:
            print("\nLogging stopped safely.")

if __name__ == "__main__":
    log_ram_usage()
