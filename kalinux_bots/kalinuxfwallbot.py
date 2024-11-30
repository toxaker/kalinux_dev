import signal
import os
import subprocess
import requests
import re
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("firewall_bot.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()
TOKEN='your_token'
chat_id = os.getenv("ADMIN_ID")



class FirewallBuilder:
    def __init__(self):
        self.user_states = {}

    # Start command with greeting and main menu
    async def start_builder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        greeting_message = (
            "Welcome to the Firewall Bot! 🔥\n\n"
            "This bot allows you to manage firewall rules directly from Telegram.\n"
            "Please select an option below to get started."
        )
        buttons = [
            [InlineKeyboardButton("Add Rule", callback_data="menu_add_rule")],
            [InlineKeyboardButton("Show Rules", callback_data="menu_show_rules")],
            [InlineKeyboardButton("Predefined Rules", callback_data="menu_predefined_rules")],
            [InlineKeyboardButton("Delete Rule", callback_data="menu_delete_rule")],
            [InlineKeyboardButton("Baza rules", callback_data="builtin_rules")],
            [InlineKeyboardButton("Help", callback_data="menu_help")],
            [InlineKeyboardButton("Exit", callback_data="menu_exit")]
        ]
        await self.send_message(update, greeting_message, InlineKeyboardMarkup(buttons))
        logging.info(f"User {update.effective_user.id} accessed the start menu.")

    # Helper function to send a message, handling both message and callback updates
    async def send_message(self, update: Update, text: str, reply_markup=None):
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
            await update.callback_query.answer()

    # Helper function to clear user state
    def clear_user_state(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]

    # Handle main menu options
    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = update.effective_user.id

        if query.data == "menu_add_rule":
            await self.add_rule(update, context)
        elif query.data == "menu_show_rules":
            await self.show_rules(update, context)
        elif query.data == "menu_predefined_rules":
            await self.predefined_rules(update, context)
        elif query.data == "menu_delete_rule":
            await self.delete_rule(update, context)
        elif query.data == "menu_help":
            await self.help_command(update, context)
        elif query.data == "menu_exit":
            await query.message.reply_text("Goodbye! 👋")
        elif query.data == "builtin_rules":
            await builtin_rules(update, context)

    # Start rule creation process: Step 1 - Select Direction
    async def add_rule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.user_states[user_id] = {"direction": None, "protocol": None, "source_ip": None,
                                     "source_port": None, "destination_ip": None, "destination_port": None}
        logging.info(f"User {user_id} started rule creation.")

        buttons = [
            [InlineKeyboardButton("INPUT", callback_data="rule_direction_input")],
            [InlineKeyboardButton("OUTPUT", callback_data="rule_direction_output")],
            [InlineKeyboardButton("FORWARD", callback_data="rule_direction_forward")]
        ]
        await self.send_message(update, "Select the rule direction:", InlineKeyboardMarkup(buttons))

    async def handle_rule_direction(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = update.effective_user.id

        direction = query.data.split("_")[-1].upper()
        self.user_states[user_id]["direction"] = direction
        logging.info(f"User {user_id} selected direction: {direction}")

        buttons = [
            [InlineKeyboardButton("TCP", callback_data="rule_protocol_tcp")],
            [InlineKeyboardButton("UDP", callback_data="rule_protocol_udp")]
        ]
        await self.send_message(update, "Select the protocol for your rule:", InlineKeyboardMarkup(buttons))

    async def handle_protocol_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = update.effective_user.id

        protocol = query.data.split("_")[-1].upper()
        self.user_states[user_id]["protocol"] = protocol
        logging.info(f"User {user_id} selected protocol: {protocol}")

        buttons = [[InlineKeyboardButton("Any", callback_data="source_ip_any")]]
        await self.send_message(update, "Please enter the Source IP address:", InlineKeyboardMarkup(buttons))

    async def handle_source_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        source_ip = update.message.text.strip()

        if source_ip.lower() == "any":
            self.user_states[user_id]["source_ip"] = "any"
        elif not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", source_ip):
            await update.message.reply_text("Invalid IP address. Please enter a valid Source IP or select 'Any'.")
            return
        else:
            self.user_states[user_id]["source_ip"] = source_ip

        buttons = [[InlineKeyboardButton("Any", callback_data="source_port_any")]]
        await update.message.reply_text("Please enter the Source Port:", reply_markup=InlineKeyboardMarkup(buttons))

    async def handle_source_port(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        source_port = update.message.text.strip()

        if source_port.lower() == "any":
            self.user_states[user_id]["source_port"] = "any"
        elif not source_port.isdigit() or not (1 <= int(source_port) <= 65535):
            await update.message.reply_text("Invalid port. Please enter a valid Source Port or select 'Any'.")
            return
        else:
            self.user_states[user_id]["source_port"] = source_port

        buttons = [[InlineKeyboardButton("Any", callback_data="destination_ip_any")]]
        await update.message.reply_text("Please enter the Destination IP address:", reply_markup=InlineKeyboardMarkup(buttons))

    async def handle_destination_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        destination_ip = update.message.text.strip()

        if destination_ip.lower() == "any":
            self.user_states[user_id]["destination_ip"] = "any"
        elif not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", destination_ip):
            await update.message.reply_text("Invalid IP address. Please enter a valid Destination IP or select 'Any'.")
            return
        else:
            self.user_states[user_id]["destination_ip"] = destination_ip

        buttons = [[InlineKeyboardButton("Any", callback_data="destination_port_any")]]
        await update.message.reply_text("Please enter the Destination Port:", reply_markup=InlineKeyboardMarkup(buttons))

    async def handle_destination_port(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        destination_port = update.message.text.strip()

        if destination_port.lower() == "any":
            self.user_states[user_id]["destination_port"] = "any"
        elif not destination_port.isdigit() or not (1 <= int(destination_port) <= 65535):
            await update.message.reply_text("Invalid port. Please enter a valid Destination Port or select 'Any'.")
            return
        else:
            self.user_states[user_id]["destination_port"] = destination_port

        rule = self.user_states[user_id]
        confirmation_message = (
            f"Your rule:\nDirection: {rule['direction']}\nProtocol: {rule['protocol']}\n"
            f"Source IP: {rule['source_ip']} Port: {rule['source_port']}\n"
            f"Destination IP: {rule['destination_ip']} Port: {rule['destination_port']}\n\n"
            "Do you want to execute this rule?"
        )
        buttons = [
            [InlineKeyboardButton("Confirm", callback_data="confirm_rule")],
            [InlineKeyboardButton("Cancel", callback_data="cancel_rule")]
        ]
        await self.send_message(update, confirmation_message, InlineKeyboardMarkup(buttons))

    async def handle_rule_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = update.effective_user.id
        rule = self.user_states.get(user_id)

        if query.data == "confirm_rule" and rule:
            try:
                # Simulating rule execution
                result_message = "Rule executed successfully!"
                logging.info(f"User {user_id} executed rule: {rule}")
            except Exception as e:
                result_message = f"Error executing rule: {e}"
                logging.error(result_message)
            self.clear_user_state(user_id)
        else:
            result_message = "Rule creation canceled."
            self.clear_user_state(user_id)

        await query.message.reply_text(result_message)
        await query.answer()

    async def show_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all current iptables rules."""
        try:
            result = subprocess.run(["iptables", "-L", "-n", "-v"], stdout=subprocess.PIPE, text=True)
            rules = result.stdout if result.returncode == 0 else "Error fetching rules."
        except Exception as e:
            rules = f"Failed to retrieve rules: {e}"

        await update.callback_query.message.reply_text(f"Current Rules:\n\n{rules}")
        await update.callback_query.answer()

    async def delete_rule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a specific rule."""
        try:
            # Example placeholder for listing and deleting rules
            await update.callback_query.message.reply_text("Feature to delete rules coming soon.")
        except Exception as e:
            await update.callback_query.message.reply_text(f"Error: {e}")
        await update.callback_query.answer()

    async def predefined_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Apply predefined rulesets."""
        rulesets = {
            "SSH Protection": ["iptables -A INPUT -p tcp --dport 22 -j ACCEPT"],
            "HTTP/HTTPS Protection": [
                "iptables -A INPUT -p tcp --dport 80 -j ACCEPT",
                "iptables -A INPUT -p tcp --dport 443 -j ACCEPT"
            ],
            "Block All Except Local": [
                "iptables -A INPUT -i lo -j ACCEPT",
                "iptables -A INPUT -j DROP"
            ],
            "all": [
            "iptables -F",
            "iptables -X",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT ACCEPT",
            "iptables -A INPUT -p udp -s 0.0.0.0 -d 0.0.0.0 -j ACCEPT",
            "iptables -A INPUT -p udp -s 255.255.255.255 -d 0.0.0.0 -j ACCEPT",
            "iptables -A INPUT -p tcp -s 185.203.1.214 --dport 16661 -j ACCEPT",
            "iptables -A INPUT -d 127.0.1.1 -s 127.0.0.1 -j ACCEPT",
            "iptables -A INPUT -d 127.0.0.1 -s 127.0.1.1 -j ACCEPT",
            "iptables -A INPUT -d 0.0.0.0 -s 127.0.0.1 -j ACCEPT",
            "iptables -A INPUT -d 0.0.0.0 -s 127.0.1.1 -j ACCEPT",
            "iptables -A INPUT -p tcp -s 185.203.1.214 -j ACCEPT",
            "iptables -A INPUT -i lo -j ACCEPT",
            "iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT",
            "iptables -A INPUT -p icmp -j ACCEPT",
            "iptables -A INPUT -p tcp --dport 50000:60000 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn --dport 80 -m connlimit --connlimit-above 100 -j REJECT",
            "iptables -A INPUT -m limit --limit 3/hour --limit-burst 10 -j ACCEPT",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL SYN,FIN,PSH,URG -j DROP"
            "iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP",
            "iptables -A INPUT -j LOG --log-prefix 'Blocked Input:' --log-level 4",
            "iptables -A INPUT -f -j DROP",
            "iptables -A INPUT -m state --state INVALID -j DROP",
            "iptables -A INPUT -p tcp -s 127.0.0.1 --dport 6379 -j ACCEPT",
            "iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags FIN,URG,PSH FIN,URG,PSH -j DROP",
            "iptables -A INPUT -p tcp --syn -m connlimit --connlimit-above 10 -j REJECT",
            "iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL ACK -m limit --limit 5/s --limit-burst 10 -j ACCEPT",
            "iptables -A INPUT -p tcp --tcp-flags ALL ACK -j DROP",
            "iptables -A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 20 -j DROP",
            "iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -m limit --limit 10/s --limit-burst 20 -j ACCEPT",
            "iptables -A INPUT -p tcp --dport 80 -j DROP",
            "iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 4 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn -j DROP",
            "iptables -A INPUT -p tcp --dport 80 -m string --string 'User-Agent: Slowloris' --algo bm -j DROP",
            "iptables -A INPUT -p icmp -m limit --limit 1/s --limit-burst 5 -j ACCEPT",
            "iptables -A INPUT -p icmp -j DROP",
            ],

        }

        buttons = [
            [InlineKeyboardButton(name, callback_data=f"apply_ruleset_{name}")]
            for name in rulesets.keys()
        ]
        await self.send_message(update, "Select a predefined ruleset to apply:", InlineKeyboardMarkup(buttons))
        context.chat_data["rulesets"] = rulesets

    def run_command(self, command):
        try:
            subprocess.run(command, check=True, shell=True)
            time.sleep(0.1)
        except subprocess.CalledProcessError as e:
            print(f"Ошибка выполнения команды: {e}")

    def allow_tcport(self, port, protocol="tcp"):
        self.run_command(f"iptables -A INPUT -p {protocol} --dport {port} -j ACCEPT")

    def allow_udport(self, port, protocol="udp"):
        self.run_command(f"iptables -A INPUT -p {protocol} --dport {port} -j ACCEPT")

    def save_rules(self):
        self.run_command("iptables-save > /etc/iptables/rules.v4")

    def load_rules(self):
        self.run_command("iptables-restore < /etc/iptables/rules.v4")

    async def builtrules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
           buttons = [
               [InlineKeyboardButton("Yes", callback_data="builtin_rules")],
               [InlineKeyboardButton("Cancel", callback_data="start_builder")]
           ]
           await context.bot.send_message(chat_id=update.effective_chat.id, text="Применены стандартные правила!", reply_markup=InlineKeyboardMarkup(authenticated_menu_buttons))

    async def builtin_rules(self):
        commands = [
            "iptables -F",
            "iptables -X",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT ACCEPT",
            "iptables -A INPUT -p udp -s 0.0.0.0 -d 0.0.0.0 -j ACCEPT",
            "iptables -A INPUT -p udp -s 255.255.255.255 -d 0.0.0.0 -j ACCEPT",
            "iptables -A INPUT -p tcp -s 185.203.1.214 --dport 16661 -j ACCEPT",
            "iptables -A INPUT -d 127.0.1.1 -s 127.0.0.1 -j ACCEPT",
            "iptables -A INPUT -d 127.0.0.1 -s 127.0.1.1 -j ACCEPT",
            "iptables -A INPUT -d 0.0.0.0 -s 127.0.0.1 -j ACCEPT",
            "iptables -A INPUT -d 0.0.0.0 -s 127.0.1.1 -j ACCEPT",
            "iptables -A INPUT -p tcp -s 185.203.1.214 -j ACCEPT",
            "iptables -A INPUT -i lo -j ACCEPT",
            "iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT",
            "iptables -A INPUT -p icmp -j ACCEPT",
            "iptables -A INPUT -p tcp --dport 50000:60000 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn --dport 80 -m connlimit --connlimit-above 100 -j REJECT",
            "iptables -A INPUT -m limit --limit 3/hour --limit-burst 10 -j ACCEPT",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL SYN,FIN,PSH,URG -j DROP"
            "iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP",
            "iptables -A INPUT -j LOG --log-prefix 'Blocked Input:' --log-level 4",
            "iptables -A INPUT -f -j DROP",
            "iptables -A INPUT -m state --state INVALID -j DROP",
            "iptables -A INPUT -p tcp -s 127.0.0.1 --dport 6379 -j ACCEPT",
            "iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags FIN,URG,PSH FIN,URG,PSH -j DROP",
            "iptables -A INPUT -p tcp --syn -m connlimit --connlimit-above 10 -j REJECT",
            "iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL ACK -m limit --limit 5/s --limit-burst 10 -j ACCEPT",
            "iptables -A INPUT -p tcp --tcp-flags ALL ACK -j DROP",
            "iptables -A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 20 -j DROP",
            "iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -m limit --limit 10/s --limit-burst 20 -j ACCEPT",
            "iptables -A INPUT -p tcp --dport 80 -j DROP",
            "iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 4 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn -j DROP",
            "iptables -A INPUT -p tcp --dport 80 -m string --string 'User-Agent: Slowloris' --algo bm -j DROP",
            "iptables -A INPUT -p icmp -m limit --limit 1/s --limit-burst 5 -j ACCEPT",
            "iptables -A INPUT -p icmp -j DROP",
            ],

        for command in commands:
            self.run_command(command, "builtin_rules")


    async def handle_ruleset_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Apply the selected predefined ruleset."""
        query = update.callback_query
        ruleset_name = query.data.split("_", 1)[1]
        rulesets = context.chat_data.get("rulesets", {})

        if ruleset_name in rulesets:
            try:
                for rule in rulesets[ruleset_name]:
                    subprocess.run(rule.split(), check=True)
                result_message = f"Predefined ruleset '{ruleset_name}' applied successfully."
            except Exception as e:
                result_message = f"Failed to apply ruleset '{ruleset_name}': {e}"
        else:
            result_message = f"Ruleset '{ruleset_name}' not found."

        await query.message.reply_text(result_message)
        await query.answer()

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display help information."""
        help_text = (
            "This bot allows you to manage firewall rules via Telegram.\n\n"
            "Available commands:\n"
            "/start - Start the bot\n"
            "Main Menu Options:\n"
            "- Add Rule: Create and apply a new firewall rule.\n"
            "- Show Rules: Display all current firewall rules.\n"
            "- Predefined Rules: Quickly apply common firewall configurations.\n"
            "- Delete Rule: Remove an existing firewall rule.\n"
            "- Help: View usage instructions.\n"
            "- Exit: Close the bot interface.\n\n"
            "Contact your system administrator for additional support."
        )
        await self.send_message(update, help_text)

# Main execution
if __name__ == "__main__":
    builder = FirewallBuilder()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", builder.start_builder))
    app.add_handler(CallbackQueryHandler(builder.handle_menu, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(builder.handle_ruleset_application, pattern="^apply_ruleset_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, builder.handle_source_ip))

    logging.info("Bot is starting...")
    app.run_polling()
