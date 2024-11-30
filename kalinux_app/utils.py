import logging
import re
import subprocess
import requests

class Utils:

    @staticmethod
    def log_ip_access(endpoint_name):
        """Logs visitor IP access for a given endpoint."""
        user_ip = (
            request.headers.get("X-Real-IP")
            or request.headers.get("X-Forwarded-For")
            or request.remote_addr
        )
        if user_ip:
            logging.info(f"Visitor with IP {user_ip} accessed {endpoint_name}")
        else:
            logging.warning(f"Unable to retrieve visitor's IP address for {endpoint_name}")


    @staticmethod
    def is_valid_ip(ip):
        """Validates IP address format."""
        ip_regex = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
        return bool(re.match(ip_regex, ip))


    @staticmethod
    def execute_whois(ip):
        """Executes a WHOIS lookup for an IP and returns the result."""
        try:
            result = subprocess.run(
                ["whois", ip], capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f"WHOIS lookup failed for IP {ip}: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    def network_activity():
        net_io = psutil.net_io_counters()
        return f"Bytes Sent: {net_io.bytes_sent}, Bytes Received: {net_io.bytes_recv}"

