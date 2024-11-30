#!/bin/bash

# Script to set up the development security environment

set -e

# Ensure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root." >&2
  exit 1
fi

# Read package name from user input
read -p "Enter the package name: " PACKAGE_NAME
if [ -z "$PACKAGE_NAME" ]; then
  echo "Package name cannot be empty!" >&2
  exit 1
fi

# Step 1: Create a directory under /var/www/ and move into it
TARGET_DIR="/var/www/$PACKAGE_NAME"
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR" || { echo "Failed to move to $TARGET_DIR"; exit 1; }

echo "Created and moved to directory: $TARGET_DIR"

# Step 2: Install required tools
echo "Installing required tools..."
apt update && apt install -y clamav chkrootkit rkhunter lynis iptables ipset fail2ban \
nginx apache2 python3 python3-pip python3-dev build-essential libssl-dev \
libffi-dev python3-setuptools certbot python3-certbot-nginx nmap nload \
iptraf nmon acct sysstat rsyslog aide auditd git htop needrestart apt-show-versions apt-listbugs redis || {
  echo "Failed to install required tools."; exit 1; }

echo "Tools installed successfully."

# Step 3: Create and activate Python virtual environment
echo "Creating and activating Python virtual environment..."
python3 -m venv kdevsecenv || { echo "Failed to create virtual environment."; exit 1; }
source kdevsecenv/bin/activate || { echo "Failed to activate virtual environment."; exit 1; }

echo "Python virtual environment activated."

# Step 4: Upgrade pip and install Python dependencies
echo "Upgrading pip and installing Python dependencies..."
pip install --upgrade pip setuptools || { echo "Failed to upgrade pip."; exit 1; }

if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt || { echo "Failed to install dependencies."; exit 1; }
else
  echo "requirements.txt not found in $TARGET_DIR. Skipping dependency installation."
fi

# Step 5: Replace weak default configurations with strong configurations
echo "Replacing default configuration files with strong ones..."
CONFIG_DIR="/var/username/kalinux_devsec"

for CONFIG_FILE in "jail.local" "nginx.conf" "sshd_config"; do
  SOURCE_FILE="$CONFIG_DIR/$CONFIG_FILE"
  TARGET_FILE=""
  
  case $CONFIG_FILE in
    "jail.local") TARGET_FILE="/etc/fail2ban/jail.local";;
    "nginx.conf") TARGET_FILE="/etc/nginx/nginx.conf";;
    "sshd_config") TARGET_FILE="/etc/ssh/sshd_config";;
  esac

  if [ -f "$SOURCE_FILE" ]; then
    [ -f "$TARGET_FILE" ] && mv "$TARGET_FILE" "${TARGET_FILE}.backup"
    mv "$SOURCE_FILE" "$TARGET_FILE"
    
    case $CONFIG_FILE in
      "jail.local") systemctl restart fail2ban;;
      "nginx.conf") systemctl restart nginx;;
      "sshd_config") systemctl restart sshd;;
    esac

    echo "$CONFIG_FILE configuration replaced and service restarted."
  else
    echo "Custom $CONFIG_FILE not found. Skipping."
  fi
done

echo "Configuration updates completed."

# Step 6: Notify user that the script is done
echo "Setup is complete. You can add further steps if needed."

exit 0
