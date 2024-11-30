import requests
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from .models import User
from .utils import Utils
from .preventer import IntrusionDetector

api_bp = Blueprint('api', __name__)
intrusion_detector = IntrusionDetector()  # Initialize the intrusion detector
limiter = Limiter(key_func=get_remote_address)


def log_ip_access(endpoint_name):
    user_ip = (
        request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For")
        or request.remote_addr
    )
    if user_ip:
        logging.info(f"Someone with IP {user_ip} accessed {endpoint_name}")
        if intrusion_detector.is_ip_banned(user_ip):  # Check if IP is banned
            return "Access denied. Your IP is banned.", 403
    else:
        logging.warning(f"Unable to retrieve visitor's IP address for {endpoint_name}")


@api_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            log_ip_access("login")
        else:
            flash("Invalid username or password.", "danger")
            log_ip_access("failed login attempt")
        return redirect(url_for("admin"))
    return render_template("login.html")


@api_bp.route('/loginadmin', methods=['POST'])
def loginadmin():
    honeypot = request.form.get('honeypot', '')
    if honeypot:
        log_ip_access("honeypot triggered")
        return "Access denied.", 403


@api_bp.route('/trap')
def trap():
    ip = request.remote_addr
    intrusion_detector.ban_ip(ip)  # Ban IP
    log_ip_access("trap triggered")
    return "IP banned.", 403

@api_bp.route('/invisible-page')
def invisible_page():
    ip = request.remote_addr
    intrusion_detector.ban_ip(ip)  # Ban IP
    log_ip_access("invisible page triggered")
    return "Bot detected and logged.", 403


@api_bp.route("/detect_intrusions", methods=["GET"])
def detect_intrusions():
    """Route to trigger manual intrusion detection."""
    result = intrusion_detector.detect_intrusions()
    return jsonify({"message": result})


@api_bp.route("/admin", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("bothasnoname")
        password = request.form.get("bot_ovodpid_or")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            log_ip_access("fakelogin trigger")
        return redirect(url_for("/admin.html"))
        flash("Invalid username or password.", "danger")
    log_ip_access("fake triggered")
    return render_template("login.html")


@api_bp.route('/loginadmin', methods=['POST'])
def loginadmin():
    honeypot = request.form.get('honeypot', '')

    if honeypot:  # Если поле заполнено
        log_ip_access("Bot detected! Access {ip} denied.")
        return "Access denied.", 403


@api_bp.route('/trap')
def trap():
    log_ip_access("Bot detected! Access {ip} denied.")
    return "IP banned.", 403


@api_bp.route('/invisible-page')
def invisible_page():
    ip = request.remote_addr
    with open("/var/www/kalinuxsec/akalia_dev/app.log", "a") as log_file:
        log_file.write(f"Trap triggered by IP: {ip}\n")
    return "Bot detected and logged.", 403

@api_bp.route("/")
@limiter.limit("10 per minute")
def index():
    log_ip_access("Captcha and it works!")
    return render_template("index.html")

@api_bp.route("/home")
@limiter.limit("10 per minute")
def home():
    log_ip_access("Home and default works!")
    return render_template("home.html")


@api_bp.route("/tutorial")
def tutorial():
    log_ip_access("Tutorial Page")
    return render_template("tutorial.html")


@api_bp.route("/letsgoauth")
@limiter.limit("5 per minute")
def letsgoauth():
    log_ip_access("Auth Page")
    return render_template("letsgoauth.html")


@api_bp.route("/webdownload")
@limiter.limit("5 per minute")
def webdownload():
    log_ip_access("Web Download Page")
    return render_template("webdownload.html")


@api_bp.route("/dashpanel")
@limiter.limit("10 per minute")
def dashpanel():
    log_ip_access("Dashpanel page")
    return render_template("dashpanel.html")


@api_bp.route("/secure/dashpanelda")
def dashpanelda():
    log_ip_access("Secure Bot Menu Page")
    return render_template("secure/dashpanelda.html")


@api_bp.route("/secure/scantools")
def scantools():
    log_ip_access("Scan Tools Page")
    return render_template("scantools.html")


@api_bp.route("/secure/webtools")
def webtools():
    log_ip_access("Web Tools Page")
    return render_template("webtools.html")


@api_bp.route("/secure/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("routes.login"))


@api_bp.route("/secure/clientside")
def clientside():
    log_ip_access("Client-Side Page")
    return render_template("clientside4.html")


@api_bp.route("/secure/toolsmenu")
def toolsmenu():
    log_ip_access("Tools Menu")
    return render_template("toolsmenu.html")


@api_bp.route("/secure/botmenu")
def botmenu():
    log_ip_access("Botmenu page")
    return render_template("botmenu.html")
