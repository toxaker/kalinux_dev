#!/bin/bash

# Script to set up the development security environment

# Exit on error
set -e

# Ensure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root." >&2
  exit 1
fi

# Read package name from user input
read -p "Enter the package name: " PACKAGE_NAME

# Step 1: Create a directory under /var/www/ and move into it
mkdir -p /var/www/"$PACKAGE_NAME"

TARGET_DIR=/var/www/"$PACKAGE_NAME"

tar -xf "$PACKAGE_NAME" "TARGET_DIR"

cd "$TARGET_DIR"

echo "Created and moved to directory: $TARGET_DIR"

# Step 2: Install required tools
echo "Installing required tools..."
apt update
apt install -y clamav chkrootkit rkhunter lynis iptables ipset fail2ban \
nginx apache2 python3 python3-pip python3-dev build-essential libssl-dev \
libffi-dev python3-setuptools certbot python3-certbot-nginx nmap nload \
iptraf nmon acct sysstat rsyslog aide auditd git htop needrestart apt-show-versions apt-listbugs redis

echo "Tools installed successfully."

# Step 3: Create and activate Python virtual environment
echo "Creating and activating Python virtual environment..."
python3 -m venv kdevsecenv
source kdevsecenv/bin/activate

echo "Python virtual environment activated."

# Step 4: Upgrade pip and install Python dependencies
echo "Upgrading pip and installing Python dependencies..."
pip install --upgrade pip setuptools

if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  echo "requirements.txt not found in $TARGET_DIR. Skipping dependency installation."
fi

# Step 5: Replace weak default configurations with strong configurations
echo "Replacing default configuration files with strong ones..."

# Example configurations (replace with your actual paths)
if [ -f "/var/username/kalinux_devsec/jail.local" ]; then
  mv /etc/fail2ban/jail.conf /etc/fail2ban/jaildefaultconf.txt
  mv /var/username/kalinux_devsec/jail.local /etc/fail2ban/jail.local
  systemctl restart fail2ban
  echo "fail2ban configuration replaced and restarted."
else
  echo "Custom fail2ban configuration not found. Skipping."
fi

if [ -f "/var/username/kalinux_devsec/nginx.conf" ]; then
  mv /etc/nginx/nginx.conf /etc/nginx/nginxdefaultconf.txt
  mv /var/username/kalinux_devsec/nginx.conf /etc/nginx/nginx.conf
  systemctl restart nginx
  echo "nginx configuration replaced and restarted."
else
  echo "Custom nginx configuration not found. Skipping."
fi

if [ -f "/var/username/kalinux_devsec/sshd_config" ]; then
  mv /etc/ssh/sshd_config /etc/ssh/sshddefaultconf.txt
  mv /var/username/kalinux_devsec/sshd_config /etc/ssh/sshd_config
  systemctl restart sshd
  echo "sshd configuration replaced and restarted."
else
  echo "Custom sshd configuration not found. Skipping."
fi

echo "Configuration updates completed."

# Step 6: Notify user that the script is done
echo "Setup is complete. You can add further steps if needed."

# Exit the script
exit 0
