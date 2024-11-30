
from flask import Flask, Blueprint, request, jsonify, render_template, flash
import subprocess
import psutil
import ssl
import socket
from datetime import datetime
import re
import logging
import requests
from .models import db, FirewallRule, LogEntry
from .utils import Utils
from .preventer import IntrusionDetector

api_bp = Blueprint("api", __name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
intrusion_detector = IntrusionDetector()
ALLOWED_ACTIONS = {"start", "stop"}
ALLOWED_PROCESSES = {"status", "reboot"} 


@api_bp.route('/trap')
def trap():
    ip = request.remote_addr
    intrusion_detector.ban_ip(ip)
    log_ip_access("Stpd bot got foreverban")
    ban_ip(ip)
    return jsonify({"error": "Bot detected and logged"}), 403


@api_bp.route("/detect_intrusions", methods=["GET"])
def detect_intrusions():
    result = intrusion_detector.detect_intrusions()
    log_ip_access("message", "{ip}")


@api_bp.route('/loginadmin', methods=['POST'])
def loginadmin():
    honeypot = request.form.get('honeypot', '')
    if honeypot:
        ip = request.remote_addr
        log_trap(ip, "Honeypot triggered")
        block_ip(ip)
        return jsonify({"error": "Access Denied"}), 403


def log_trap(ip, message):
    log_file = '/var/www/kalinuxsec/akalia_dev/app.log'
    with open(log_file, 'a') as f:
        f.write(f"{message} by IP: {ip}\n")


def validate_target(target):
    ip_regex = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    domain_regex = r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}$"
    if not re.match(ip_regex, target) and not re.match(domain_regex, target):
        raise ValueError("Invalid target. Must be a valid IP or domain.")


def make_response(data=None, error=None, status=200):
    """Utility function to create a standardized response."""
    response = {"success": error is None}
    if data:
        response["data"] = data
    if error:
        response["error"] = error
    return jsonify(response), status


def log_trap(ip, message):
    log_file = '/var/www/kalinuxsec/akalia_dev/app.log'
    with open(log_file, 'a') as f:
        f.write(f"{message} by IP: {ip}\n")

def make_response(data=None, error=None, status=200):
    if error:
        return jsonify({"success": False, "error": error}),
    return jsonify({"success": True}), status

def validate_target(target):
    ip_regex = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    domain_regex = r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}$"
    if not re.match(ip_regex, target) and not re.match(domain_regex):
        raise ValueError("Invalid target. Must be a valid IP or domain.")

# Add a function to reset the intrusion detector
def reset_intrusion_detector():
    """Reset temporary and permanent bans."""
    intrusion_detector.reset()
    logging.info("Intrusion detector reset.")



@api_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("dummyname")
        password = request.form.get("dummybot")
#        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            log_ip_access("login")
        else:
            flash("Invalid username or password.", "danger")
            log_ip_access("failed login attempt")
        return redirect(url_for("admin.html"))
    return render_template("login.html")


@api_bp.route("/scan", methods=["POST"])
def perform_scan():
    scan_type = request.form.get("scan_type")
    target = request.form.get("target")
    scan_command = available_commands[scan_type] + [target]

    
    available_commands = {
        "ping": ["ping", "-c", "4"],
        "traceroute": ["traceroute"],
        "port_scan": ["nmap", "-p", "1-1000"],
        "nikto": ["nikto", "-h"],
        "whois": ["whois"],
    }
    
    try:
        validate_target(target)
        if scan_type not in available_commands:
            return make_response(error="Invalid scan type", status=400)
                
        if scan_type == "ssl_checker":
            context = ssl.create_default_context()
            with socket.create_connection((target, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=target) as ssock:
                    cert = ssock.getpeercert()
                    expiration = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    return make_response(data={
                        "SSL Expiration": expiration.isoformat(),
                        "Issuer": cert.get("issuer"),
                        "Subject": cert.get("subject"),
                    })
        
        # Execute the predefined command securely
        result = subprocess.run(scan_command, capture_output=True, text=True, check=True)
        return make_response(data=result.stdout)
    
    except subprocess.CalledProcessError as cpe:
        logging.error(f"Command execution failed: {cpe}")
        return make_response(error="Command execution failed", status=500)
    except ValueError as ve:
        return make_response(error=str(ve), status=400)
    except Exception as e:
        logging.error(f"Error during scan: {e}")
        return make_response(error="Scan failed", status=500)


def ban_ip(ip):
    try:
        jail_name = "custom-trap"
        command = f"'fail2ban-client set' '{jail_name}' 'banip {ip}'"
        subprocess.run(command, shell=True, check=True)
        print(f"IP {ip} заблокирован через fail2ban.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при блокировке IP {ip}: {e}")


@api_bp.route("/block_ip", methods=["POST"])
def block_ip():
    data = request.json
    ip = data.get("ip")
    try:
        if not ip:
            raise ValueError("IP address is required.")
        Utils.add_ip_block(ip)
        return make_response(data=f"Blocked IP: {ip}")
    except Exception as e:
        logging.error(f"Failed to block IP: {e}")
        return make_response(error=str(e), status=500)

@api_bp.route("/unblock_ip", methods=["POST"])
def unblock_ip():
    data = request.json
    ip = data.get("ip")
    try:
        Utils.remove_ip_block(ip)
        return make_response(data=f"Unblocked IP: {ip}")
    except Exception as e:
        logging.error(f"Failed to unblock IP: {e}")
        return make_response(error=str(e), status=500)

@api_bp.route("/dns_lookup", methods=["POST"])
def dns_lookup():
    data = request.json
    domain = data.get("domain")
    try:
        dns_records = socket.gethostbyname_ex(domain)
        return make_response(data={"dns_records": dns_records})
    except Exception as e:
        logging.error(f"DNS lookup failed: {e}")
        return make_response(error="DNS lookup failed", status=500)

@api_bp.route("/reverse_dns_lookup", methods=["POST"])
def reverse_dns_lookup():
    data = request.json
    ip = data.get("ip")
    try:
        reverse_dns = socket.gethostbyaddr(ip)
        return make_response(data={"reverse_dns": reverse_dns})
    except Exception as e:
        logging.error(f"Reverse DNS lookup failed: {e}")
        return make_response(error="Reverse DNS lookup failed", status=500)

@api_bp.route("/system_metrics", methods=["GET"])
def get_system_metrics():
    try:
        metrics = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_received": psutil.net_io_counters().bytes_recv,
            },
        }
        return make_response(data=metrics)
    except Exception as e:
        logging.error(f"Failed to fetch system metrics: {e}")
        return make_response(error="Failed to fetch metrics", status=500)


def make_response(data=None, error=None, status=200):
    response = {"success": error is None}
    if data:
        response["data"] = data
    if error:
        response["error"] = error
    return jsonify(response), status

@api_bp.route("/processes", methods=["GET", "POST"])
def manage_processes():
    if request.method == "GET":
        try:
            # Restrict process details to avoid sensitive information leakage
            processes = [{"pid": p.pid, "name": p.name()} for p in psutil.process_iter(attrs=['pid', 'name'])]
            return make_response(data=processes)
        except Exception as e:
            logging.error(f"Failed to list processes: {e}")
            return make_response(error="Failed to list processes", status=500)

    elif request.method == "POST":
        action = request.json.get("action")
        process_name = request.json.get("process_name")
        pid = request.json.get("pid")

        # Validate action
        if action not in ALLOWED_ACTIONS:
            return make_response(error="Invalid action", status=400)

        # Validate process name
        if action == "start" and process_name not in ALLOWED_PROCESSES:
            return make_response(error="Process not allowed", status=403)

        try:
            if action == "start" and process_name:
                # Start a whitelisted process
                result = subprocess.Popen([process_name])
                logging.info(f"Started allowed process: {process_name}, PID: {result.pid}")
                return make_response(data={"message": f"Started process {process_name}", "pid": result.pid})

            elif action == "stop" and pid:
                # Stop a process by PID
                process = psutil.Process(pid)
                if process.name() not in ALLOWED_PROCESSES:
                    return make_response(error="Process not allowed to stop", status=403)
                process.terminate()
                logging.info(f"Terminated process: {process.name()} (PID: {pid})")
                return make_response(data={"message": f"Terminated process with PID {pid}"})

        except psutil.NoSuchProcess:
            logging.error(f"Process with PID {pid} does not exist")
            return make_response(error="Process not found", status=404)
        except Exception as e:
            logging.error(f"Failed to perform action on process: {e}")
            return make_response(error="Action failed", status=500)

    return make_response(error="Invalid request method", status=405)


@api_bp.route("/get_ip_info", methods=["POST"])
def get_ip_info():
    data = request.json
    ip = data.get("ip", request.remote_addr)
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            return make_response(data=response.json())
        return make_response(error="Failed to fetch IP information", status=500)
    except Exception as e:
        logging.error(f"Failed to fetch IP info: {e}")
        return make_response(error=str(e), status=500)

@api_bp.route("/firewall_rules", methods=["GET", "POST"])
def manage_firewall_rules():
    if request.method == "GET":
        try:
            rules = FirewallRule.query.all()
            return make_response(data=[rule.to_dict() for rule in rules])
        except Exception as e:
            logging.error(f"Failed to fetch firewall rules: {e}")
            return make_response(error="Failed to fetch rules", status=500)
    elif request.method == "POST":
        data = request.json
        try:
            rule = FirewallRule(
                direction=data['direction'],
                protocol=data['protocol'],
                source_ip=data.get('source_ip', 'any'),
                source_port=data.get('source_port', 'any'),
                destination_ip=data.get('destination_ip', 'any'),
                destination_port=data.get('destination_port', 'any'),
            )
            db.session.add(rule)
            db.session.commit()
            return make_response(data=rule.to_dict(), status=201)
        except Exception as e:
            logging.error(f"Failed to add firewall rule: {e}")
            return make_response(error="Failed to add rule", status=500)

@api_bp.route("/logs", methods=["GET"])
def get_logs():
    try:
        logs = LogEntry.query.all()
        return make_response(data=[log.to_dict() for log in logs])
    except Exception as e:
        logging.error(f"Failed to fetch logs: {e}")
        return make_response(error="Failed to fetch logs", status=500)