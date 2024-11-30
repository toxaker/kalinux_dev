import logging
from collections import defaultdict
import re
from typing import List, Tuple
from datetime import datetime
from models import LogEntry, db

class LogAnalyzer:
    def __init__(self, auth_log_path="/var/log/auth.log", iptables_log_path="/var/log/iptables.log"):
        self.auth_log_path = auth_log_path
        self.iptables_log_path = iptables_log_path
        self.banned_ips = set()
        self.visit_count = defaultdict(int)

    def read_log(self, log_path: str) -> List[str]:
        try:
            with open(log_path, 'r') as file:
                return file.readlines()
        except FileNotFoundError:
            logging.error(f"Log file {log_path} not found.")
            return []

    def analyze_auth_log(self):
        failed_attempts = 0
        suspicious_ips = []

        for line in self.read_log(self.auth_log_path):
            if "Failed password" in line:
                failed_attempts += 1
                ip = self.extract_ip(line)
                if ip:
                    suspicious_ips.append(ip)
                    self.save_log("auth", line, ip)
            elif "banned" in line:
                ip = self.extract_ip(line)
                if ip:
                    self.banned_ips.add(ip)
                    self.save_log("auth", line, ip)

        logging.info(f"Failed login attempts: {failed_attempts}")
        return failed_attempts, suspicious_ips

    def analyze_iptables_log(self):
        blocked_count = 0

        for line in self.read_log(self.iptables_log_path):
            if "IN=" in line and "BLOCK" in line:
                blocked_count += 1
                ip = self.extract_ip(line)
                if ip:
                    self.banned_ips.add(ip)
                    self.save_log("iptables", line, ip)

        logging.info(f"Blocked packets: {blocked_count}")
        return blocked_count

    def save_log(self, log_type, message, ip=None):
        log_entry = LogEntry(
            log_type=log_type,
            timestamp=datetime.now(),
            message=message,
            ip=ip
        )
        db.session.add(log_entry)
        db.session.commit()

    def extract_ip(self, text: str) -> str:
        match = re.search(r'[0-9]+(?:\.[0-9]+){3}', text)
        return match.group(0) if match else ""
