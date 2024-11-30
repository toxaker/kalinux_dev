import os
import subprocess
import psutil
import logging
import json
import time
from collections import defaultdict


# Configure logging with rotation
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = RotatingFileHandler("intrusion_detector.log", maxBytes=1_000_000, backupCount=5)
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)


class IntrusionDetector:
    def __init__(self, temp_ban_time=3600, perm_ban_threshold=3, ban_file="permanent_bans.json"):
        self.suspicious_ips = set()
        self.suspicious_ports = set()
        self.temp_ban_time = temp_ban_time
        self.perm_ban_threshold = perm_ban_threshold
        self.ban_file = ban_file
        self.permanent_bans = self.load_permanent_bans()
        self.ban_counter = defaultdict(int)
        self.temp_ban_tracker = {}

    def load_permanent_bans(self):
        """Load permanent bans from file."""
        if os.path.exists(self.ban_file):
            try:
                with open(self.ban_file, "r") as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Failed to load permanent bans: {e}")
        return set()

    def save_permanent_bans(self):
        """Save permanent bans to file."""
        try:
            with open(self.ban_file, "w") as f:
                json.dump(list(self.permanent_bans), f)
        except IOError as e:
            logging.error(f"Failed to save permanent bans: {e}")

    def ban_ip(self, ip):
        """Permanently ban an IP."""
        if ip not in self.permanent_bans:
            self.permanent_bans.add(ip)
            self.save_permanent_bans()
            logging.warning(f"Permanently banned IP: {ip}")

    def is_ip_banned(self, ip):
        """Check if an IP is permanently banned."""
        return ip in self.permanent_bans

    def get_fail2ban_blocked_ips(self):
        """Retrieve IPs blocked by Fail2Ban."""
        blocked_ips = []
        try:
            if subprocess.run(["which", "fail2ban-client"], stdout=subprocess.PIPE).returncode != 0:
                logging.warning("Fail2Ban is not installed or not available.")
                return blocked_ips

            jails_output = subprocess.check_output(["fail2ban-client", "status"], text=True, timeout=5)
            jails = [
                line.split(":")[1].strip()
                for line in jails_output.splitlines()
                if "Jail list:" in line
            ][0].split(", ") if "Jail list:" in jails_output else []

            for jail in jails:
                try:
                    ban_list_output = subprocess.check_output(
                        ["fail2ban-client", "status", jail], text=True, timeout=5
                    )
                    for line in ban_list_output.splitlines():
                        if "Banned IP list:" in line:
                            ips = line.split(":")[1].strip().split()
                            blocked_ips.extend(ips)
                except subprocess.CalledProcessError as e:
                    logging.error(f"Error retrieving bans for jail '{jail}': {e}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, IndexError) as e:
            logging.error(f"Error while retrieving Fail2Ban blocked IPs: {e}")
        return blocked_ips

    def detect_intrusions(self):
        """Detect intrusions based on suspicious IPs, ports, and Fail2Ban IPs."""
        self.suspicious_ips.update(self.get_fail2ban_blocked_ips())
        intrusions = []

        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.raddr:
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port

                    if remote_ip in self.permanent_bans:
                        continue
                        current_time = time.time()
                    if remote_ip in self.temp_ban_tracker:
                        if current_time >= self.temp_ban_tracker[remote_ip]:
                            del self.temp_ban_tracker[remote_ip]
                        else:
                            continue

                    if remote_ip in self.suspicious_ips or remote_port in self.suspicious_ports:
                        intrusions.append(f"IP: {remote_ip}, Port: {remote_port}")
                        self.ban_counter[remote_ip] += 1
                        if self.ban_counter[remote_ip] >= self.perm_ban_threshold:
                            self.ban_ip(remote_ip)
                        else:
                            self.temp_ban_tracker[remote_ip] = current_time + self.temp_ban_time
        except psutil.AccessDenied:
            logging.error("Access Denied to network connections.")
            return "Access Denied to network connections."
        except Exception as e:
            logging.error(f"Error checking intrusions: {e}")
            return f"Error checking intrusions: {e}"

        if intrusions:
            alert_message = f"Suspicious activity detected: {', '.join(intrusions)}"
            logging.warning(alert_message)
            return alert_message
        return "No suspicious activity detected."


def main():
    """CLI entry point."""
    detector = IntrusionDetector(temp_ban_time=3600, perm_ban_threshold=3)
    detector.add_suspicious_ports(22, 80, 443)
    result = detector.detect_intrusions()
    print(result)
    logging.info(result)


#if name == "__main__":
#    main()