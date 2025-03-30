import psutil
import time
import os
import logging
from utils import publish_message

# Load environment variables
DDOS_THRESHOLD = int(os.getenv("DDOS_THRESHOLD", 25000))
SLOWLORIS_THRESHOLD = int(os.getenv("SLOWLORIS_THRESHOLD", 50))
CPU_THRESHOLD = int(os.getenv("CPU_THRESHOLD", 85))
MEMORY_THRESHOLD = int(os.getenv("MEMORY_THRESHOLD", 85))
DISK_THRESHOLD = int(os.getenv("DISK_THRESHOLD", 90))

logging.basicConfig(level=logging.INFO)

def monitor():
    """Monitors system and publishes alerts."""
    prev_packets = psutil.net_io_counters().packets_recv

    while True:
        # DDoS Detection
        current_packets = psutil.net_io_counters().packets_recv
        pps = current_packets - prev_packets
        prev_packets = current_packets

        if pps > DDOS_THRESHOLD:
            publish_message("alerts", {"type": "DDoS", "pps": pps})
            logging.warning(f"DDoS Alert! PPS: {pps}")

        # System Health Monitoring
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        if cpu_usage > CPU_THRESHOLD:
            publish_message("alerts", {"type": "CPU", "usage": cpu_usage})

        if memory_usage > MEMORY_THRESHOLD:
            publish_message("alerts", {"type": "Memory", "usage": memory_usage})

        if disk_usage > DISK_THRESHOLD:
            publish_message("alerts", {"type": "Disk", "usage": disk_usage})

        time.sleep(5)

if __name__ == "__main__":
    monitor()
