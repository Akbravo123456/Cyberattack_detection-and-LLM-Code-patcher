import psutil
import time
import socket
import logging
import win32evtlog
import win32con
import ctypes 
import sys
import os

CONFIG = {
    "ddos_threshold": int(os.getenv("DDOS_THRESHOLD", 25000)),       
    "ddos_time_window": int(os.getenv("DDOS_TIME_WINDOW", 5)),      
    "mitigation_trigger_time": int(os.getenv("MITIGATION_TRIGGER_TIME", 10)), 
    
    "slowloris_half_open_threshold": int(os.getenv("HALF_OPEN_THRESHOLD", 50)),
    "slowloris_conn_threshold": int(os.getenv("CONCURRENT_CONN_THRESHOLD", 200)),
    "slowloris_duration_threshold": int(os.getenv("DURATION_THRESHOLD", 60)),
    
    "cpu_threshold": int(os.getenv("CPU_THRESHOLD", 85)),
    "memory_threshold": int(os.getenv("MEMORY_THRESHOLD", 85)),
    "disk_threshold": int(os.getenv("DISK_THRESHOLD", 90)),
    
    "scan_ports": [22, 80, 443, 3389, 3306, 5432, 135, 445],
    "scan_ip": os.getenv("SCAN_IP", "127.0.0.1")
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

prev_packets = psutil.net_io_counters().packets_recv
attack_start_time = None

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def elevate_privileges():
    """Automatically re-run the script with elevated privileges if needed."""
    if not is_admin():
        logging.warning("Restarting with admin privileges...")
        sys.stdout.flush()
        
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def trigger_mitigation():
    """Triggers placeholder mitigation action"""
    logging.warning("Triggering mitigation action (firewall, throttling, etc.)")
    sys.stdout.flush()

def detect_ddos():
    """Detects DDoS by calculating PPS over a time window"""
    global prev_packets, attack_start_time

    current_packets = psutil.net_io_counters().packets_recv
    pps = (current_packets - prev_packets) / CONFIG["ddos_time_window"]
    prev_packets = current_packets 

    logging.info(f"PPS: {pps} (Threshold: {CONFIG['ddos_threshold']})")
    sys.stdout.flush()

    if pps > CONFIG["ddos_threshold"]:
        if not attack_start_time:
            attack_start_time = time.time()

        elapsed = time.time() - attack_start_time
        if elapsed > CONFIG["mitigation_trigger_time"]:
            logging.warning(f"DDoS detected! {pps:.2f} PPS. Triggering mitigation.")
            sys.stdout.flush()
            trigger_mitigation()
    else:
        attack_start_time = None

def detect_slowloris():
    """Detects Slowloris attacks by monitoring half-open and long-lived connections"""
    logging.info("Monitoring for Slowloris attacks...")
    sys.stdout.flush()

    connections = psutil.net_connections(kind="inet")
    current_time = time.time()

    half_open_count = 0
    ip_connections = {}

    for conn in connections:
        ip = conn.raddr.ip if conn.raddr else "0.0.0.0"

        if conn.status in ["SYN_SENT", "SYN_RECV"]:
            half_open_count += 1

        if conn.status == "ESTABLISHED":
            if ip not in ip_connections:
                ip_connections[ip] = {'count': 0, 'timestamps': []}
            ip_connections[ip]['count'] += 1
            ip_connections[ip]['timestamps'].append(current_time)

    if half_open_count > CONFIG["slowloris_half_open_threshold"]:
        logging.warning(f"High number of half-open connections: {half_open_count}")
        logging.warning("DDoS attack detected during Slowloris check! 🚨")
        sys.stdout.flush()

    for ip, data in ip_connections.items():
        if data['count'] > CONFIG["slowloris_conn_threshold"]:
            logging.warning(f"Too many connections from {ip}: {data['count']}")
        
        if any(current_time - ts > CONFIG["slowloris_duration_threshold"] for ts in data['timestamps']):
            logging.warning(f"Long-lived connections from {ip}")
            sys.stdout.flush()

def monitor_system_health():
    """Monitors CPU, memory, and disk usage"""
    logging.info("Monitoring system health...")
    sys.stdout.flush()

    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    disk_usages = {part.mountpoint: psutil.disk_usage(part.mountpoint).percent
                   for part in psutil.disk_partitions(all=False)}

    if cpu_usage > CONFIG["cpu_threshold"]:
        logging.warning(f"High CPU Usage: {cpu_usage}%")
        sys.stdout.flush()

    if memory_usage > CONFIG["memory_threshold"]:
        logging.warning(f"High Memory Usage: {memory_usage}%")
        sys.stdout.flush()

    for mount, usage in disk_usages.items():
        if usage > CONFIG["disk_threshold"]:
            logging.warning(f"High Disk Usage on {mount}: {usage}%")
            sys.stdout.flush()

def check_open_ports():
    """Scans for unexpected open ports"""
    logging.info("Scanning for unexpected open ports...")
    sys.stdout.flush()

    open_ports = []
    for port in CONFIG["scan_ports"]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((CONFIG["scan_ip"], port)) == 0:
                open_ports.append(port)

    if open_ports:
        logging.warning(f"Unexpected open ports detected: {open_ports}")
        sys.stdout.flush()

def monitor_event_logs():
    """Monitors Windows Event Logs for security events"""
    logging.info("Monitoring Windows Event Logs...")
    sys.stdout.flush()

    server = 'localhost'
    log_type = 'Security'

    try:
        hand = win32evtlog.OpenEventLog(server, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

        events = win32evtlog.ReadEventLog(hand, flags, 0)

        for event in events:
            if event.EventID == 4625:  
                logging.warning(f"Failed login attempt: {event.StringInserts}")
                sys.stdout.flush()
            elif event.EventID == 4648: 
                logging.info(f"Successful login: {event.StringInserts}")
                sys.stdout.flush()

        win32evtlog.CloseEventLog(hand)

    except Exception as e:
        logging.error(f"Error accessing event logs: {e}")
        sys.stdout.flush()

def main():
    logging.info("Starting Combined Security Monitoring Script")
    sys.stdout.flush()
    elevate_privileges()

    while True:
        try:
            detect_ddos()
            detect_slowloris()
            monitor_system_health()
            check_open_ports()
            monitor_event_logs()

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            sys.stdout.flush()

        time.sleep(10)

if __name__ == "__main__":
    main()
