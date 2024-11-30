import socket
import psutil
import shutil
import re
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger
import logging
import random
import time
from redis import Redis
import os
import logging
import subprocess
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import requests
import aiohttp
import asyncio

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("ADMIN_ID")
API_URL = os.getenv("API_URL")
WEB_APP_URL = os.getenv("WEB_APP_URL")
WEB_DOWNLOAD_URL = os.getenv("WEB_DOWNLOAD_URL")
TUTORIAL_URL = os.getenv("TUTORIAL_URL")
default_services = ["nginx", "fail2ban", "firewall", "telegrambot", "kalinuxapp"]
admin_id = os.getenv("ADMIN_ID")




# Инициализация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка наличия токена
if not TOKEN:
    logger.error("Токен не загружен! Проверьте файл .env")

# Глобальная переменная для статуса аутентификации
authenticated_users = {}


# ========== Telegram Bot Handlers ==========


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в систему Kalinux Security! 🛡\n\n"
        "Этот бот предназначен для управления безопасностью вашего сервера и поможет отслеживать угрозы, анализировать события и управлять брандмауэром прямо из Telegram.\n\n"
        "Используйте команду /help для списка команд или нажмите кнопки меню для начала работы."
    )
    await default_menu(update, context)


# Полный список команд для помощи
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_command_text = (
        "Доступные команды:\n"
        "/start - Назадачать взаимодействие с ботом\n"
        "/info - Информация о боте\n"
        "/web - Перейти в приложение\n"
        "/webdownload - Скачать приложение\n"
        "/tutorial - Документация\n"
        "/default_menu - Главное меню\n"
        "/enter_token - Ввести API ключ\n"
        "/bye - Завершить работу с ботом\n"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=help_command_text
    )


# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception in {update}: {context.error}")
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠ Произошла ошибка! Сообщение отправлено разработчику.",
        )


async def api_authenticated_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    authenticated_menu_buttons = [
        [nlineKeyboardButton("🛠 Управление сервером", callback_data="server_management")],
        [InlineKeyboardButton("📄 Помощь", callback_data="help_command")],
    ]
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="API ключ принят. Выберите действие:",
        reply_markup=InlineKeyboardMarkup(authenticated_menu_buttons),
    )


# Полное меню управления сервером
async def default_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    default_menu_text = "Это ознакомительное меню. Здесь вы можете получить инструкции, документацию, установить приложение или просто посетить страницу разработчика. Чтобы открыть доступ к функциям, отправьте мне API токен, а также установите приложение."
    default_menu_buttons = [
        [InlineKeyboardButton("🔑 Ввести API", callback_data="enter_token")],
        [InlineKeyboardButton("💻 Приложение", url="https://t.me/kalinuxsecurity_bot/xakersec")],
        [InlineKeyboardButton("💠 Установить...", url="https://xakerneo.ru/webdownload")],
        [InlineKeyboardButton("ℹ Информация", callback_data="info")],
        [InlineKeyboardButton("📋 Список команд", callback_data="help_command")],
        [InlineKeyboardButton("📚 Гайд 'Быстрый старт'", url="https://xakerneo.ru/tutorial")],
        [InlineKeyboardButton("👋 Завершить", callback_data="bye")],
        [InlineKeyboardButton("🛠 Управление сервером", callback_data="server_management_menu")],
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=default_menu_text,
        reply_markup=InlineKeyboardMarkup(default_menu_buttons),
    )


# Server management menu
async def server_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server_menu_buttons = [
        [InlineKeyboardButton("🛠 Мониторинг", callback_data="monitor")],
        [InlineKeyboardButton("🛡 Статус Брандмауэра", callback_data="firewall_status")],
        [InlineKeyboardButton("📋 Сетевые инструменты", callback_data="network_utils_menu")],
        [InlineKeyboardButton("💼 Управление задачами", callback_data="tasks_autoset")],
        [InlineKeyboardButton("💻 Информация о системе", callback_data="system_info")],
        [InlineKeyboardButton("🧹 Очистка диска", callback_data="disk_cleanup")],
        [InlineKeyboardButton("🔄 Перезагрузить сервис", callback_data="restart_service")],
        [InlineKeyboardButton("⚙ Проверка состояния сервера", callback_data="server_health_check")],
        [InlineKeyboardButton("👋 Завершить", callback_data="bye")],
    ]

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=update.effective_message.message_id,
        text="Добро пожаловать в меню управления сервером.",
        reply_markup=InlineKeyboardMarkup(server_menu_buttons),
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = (
        "Kalinux Security — это Telegram-бот для управления защитой вашего сервера.\n\n"
        "С его помощью вы можете:\n"
        "🛠 Мониторить логи и состояние брандмауэра\n"
        "📊 Получать отчёты о попытках доступа\n"
        "⚙ Настраивать задачи для усиления защиты\n\n"
        "Простое и интуитивно понятное управление в вашем распоряжении!"
    )
    info_buttons = [
        [InlineKeyboardButton("💻 Приложение", url="https://t.me/kalinuxsecurity_bot/xakersec")],
        [InlineKeyboardButton("💠 Установить...", url="https://xakerneo.ru/webdownload")],
        [InlineKeyboardButton("📋 Список команд", callback_data="help_command")],
        [InlineKeyboardButton("📚 Гайд 'Быстрый старт'", url="https://xakerneo.ru/tutorial")],
        [InlineKeyboardButton("⬅ Назад в главное меню", callback_data="default_menu")],
        ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=info_text,
        reply_markup=InlineKeyboardMarkup(info_buttons),
        parse_mode="HTML",
    )


# Ввод API ключа и проверка
async def enter_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(text=help_command_text)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Пожалуйста, отправьте ваш API ключ."
        )


async def handle_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text
    # Проверка API ключа
    if token == TOKEN:  # Замените на реальную проверку
        authenticated_users[update.effective_chat.id] = True
        await api_authenticated_menu(update, context)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Poshel nahuy)"
        )


async def check_authenticated(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in authenticated_users:
        await update.message.reply_text("You are authenticated.")
    else:
        await update.message.reply_text("You are not authenticated.")


# Function to log out user (invalidate authentication)
async def logout_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in authenticated_users:
        del authenticated_users[update.effective_chat.id]
        await update.message.reply_text("You have been logged out.")
    else:
        await update.message.reply_text("You were not authenticated.")


# Кнопки основного меню задач


# Основной обработчик кнопок с условием для вызова меню и команд
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help_command":
        await help_command(update, context)
    elif query.data == "disk_cleanup":
        await disk_cleanup(update, context)
    elif query.data == "restart_service":
        await restart_service(update, context)
    elif query.data == "server_health_check":
        await server_health_check(update, context)
    elif query.data == "bye":
        await query.message.reply_text("До встречи!")
    elif query.data == "info":
        await info(update, context)
    elif query.data == "enter_token":
        await enter_token(update, context)
    elif query.data == "server_management_menu":
        await server_management_menu(update, context)
    elif query.data == "firewall_status":
        await firewall_status(update, context)
    elif query.data == "tasks_autoset":
        await tasks_autoset(update, context)
    elif query.data == "select_task":
        await select_task(update, context)
    elif query.data == "generate_report":
        await generate_report(update, context)
    elif query.data == "run_security_scan":
        await run_security_scan(update, context)
    elif query.data == "perform_security_scan":
        await perform_security_scan(update, context)
    elif query.data == "monitor":
        await monitor(update, context)
    elif query.data == "send_alert_to_admin":
        await send_alert_to_admin(update, context)
    elif query.data == "monitor_cpu":
        await monitor_cpu(update, context)
    elif query.data == "monitor_memory":
        await monitor_memory(update, context)
    elif query.data == "monitor_disk":
        await monitor_disk(update, context)
    elif query.data == "interactive_scan":
        await interactive_scan(update, context)
    elif query.data == "default_menu":
        await default_menu(update, context)  # возврат в главное меню
    elif query.data == "network_utils_menu":
        await network_utils_menu(update, context)  # возврат в главное меню
    elif query.data == "ping_host":
        await ping_host(update, context)
    elif query.data == "get_server_ip":
        await get_server_ip(update, context)
    elif query.data == "get_socket_status":
        await get_socket_status(update, context)
    elif query.data == "get_netstat":
        await get_netstat(update, context)
    elif query.data == "run_nmap_scan":
        await run_nmap_scan(update, context)
    elif query.data == "run_nikto_scan":
        await run_nikto_scan(update, context)
    elif query.data == "hard_sysinfo":
        await hard_sysinfo(update, context)
    elif query.data == "system_info":
        await system_info(update, context)
    elif query.data == "sysinfo_task":
        await sysinfo_task(update, context)
    elif query.data == "input_command_run":
        await input_command_run(update, context)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Unknown command"
        )


# ========== Network Utilities ==========
def get_cpu_usage():
    """Get current CPU usage as a percentage."""
    return psutil.cpu_percent(interval=1)


def get_memory_usage():
    """Get memory usage stats."""
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "used": memory.used,
        "available": memory.available,
        "percent": memory.percent,
    }


def get_disk_usage(path="/"):
    """Get disk usage stats for a specified path."""
    disk = shutil.disk_usage(path)
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": (disk.used / disk.total) * 100,
    }


async def monitor_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor CPU usage."""
    cpu_usage = get_cpu_usage()
    await context.bot.send_message(chat_id=update.effective.chat_id, text='f"Current CPU usage: {cpu_usage}%"')


async def monitor_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor memory usage."""
    memory = get_memory_usage()

# Network utilities menu
async def network_utils_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    network_utils_buttons = [
        [InlineKeyboardButton("📟 Проверка доступности", callback_data="ping_host")],
        [InlineKeyboardButton("📌 Проверка ip", callback_data="get_server_ip")],
        [InlineKeyboardButton("🖇 Сетевые соединения", callback_data="get_socket_status")],
        [InlineKeyboardButton("📊 Статистика сети", callback_data="get_netstat")],
        [InlineKeyboardButton("🗳  Менеджер задач", callback_data="tasks_autoset")],
        [InlineKeyboardButton("⬅ Назад в меню", callback_data="server_management_menu")],
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Серверные инструменты:",
        reply_markup=InlineKeyboardMarkup(network_utils_buttons),
    )


async def tasks_autoset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks_autoset_buttons = [
        [InlineKeyboardButton("📟 Сканировать...", callback_data="select_task")],
        [InlineKeyboardButton("📝 Отчёт системы безопасности", callback_data="run_security_scan")],
        [InlineKeyboardButton("🔄 Отчет компонентов системы", callback_data="sysinfo_task")],
        [InlineKeyboardButton("👽 Nmap сканер", callback_data="run_nmap_scan")],
        [InlineKeyboardButton("🥷 Nikto сканер", callback_data="run_nikto_scan")],
        [InlineKeyboardButton("⬅ Назад в меню", callback_data="server_management_menu")],
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите действие для задач:",
        reply_markup=InlineKeyboardMarkup(tasks_autoset_buttons),
    )

async def hard_sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer("Processing your request...")
    user_task = query.data.strip().lower() if query and query.data else None
    task_map = {
        "server_health_check": server_health_check,
        "generate_report": generate_report,
        "run_security_scan": run_security_scan,
        "perform_security_scan": perform_security_scan,
        "monitor_cpu": monitor_cpu,
        "monitor_memory": monitor_memory,
        "monitor_disk": monitor_disk,
    }
    task_function = task_map.get(user_task)
    if task_function:
        await task_function(update, context)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Unknown task: {user_task}. Please select a valid option."
        )

async def sysinfo_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sysinfo_task_buttons = [
        [InlineKeyboardButton("Server Health Check", callback_data="server_health_check")],
        [InlineKeyboardButton("Generate Report", callback_data="generate_report")],
        [InlineKeyboardButton("Run Security Scan", callback_data="run_security_scan")],
        [InlineKeyboardButton("Monitor CPU", callback_data="monitor_cpu")],
        [InlineKeyboardButton("Monitor Memory", callback_data="monitor_memory")],
        [InlineKeyboardButton("Monitor Disk", callback_data="monitor_disk")],
    ]
    reply_markup = InlineKeyboardMarkup(sysinfo_task_buttons)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Select a task:",
        reply_markup=reply_markup,
    )

def cached_result(key, ttl=5):
    now = time.time()
    if key not in _cache or now - _cache_time[key] > ttl:
        return None
    return _cache[key]

def update_cache(key, value):
    _cache[key] = value
    _cache_time[key] = time.time()

_cache = {"cpu": None, "memory": None, "disk": None}
_cache_time = {"cpu": 0, "memory": 0, "disk": 0}


async def monitor_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu_usage = cached_result("cpu")
    if cpu_usage is None:
        cpu_usage = psutil.cpu_percent(interval=1)
        update_cache("cpu", cpu_usage)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"CPU Usage: {cpu_usage}%")

async def monitor_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    memory_usage = cached_result("memory")
    if memory_usage is None:
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "used": memory.used,
            "percent": memory.percent,
        }
        update_cache("memory", memory_usage)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"Memory Usage:\n"
            f"Total: {memory_usage['total'] / (1024 ** 3):.2f} GB\n"
            f"Used: {memory_usage['used'] / (1024 ** 3):.2f} GB\n"
            f"Percent: {memory_usage['percent']}%"
        )
    )

async def run_security_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Starting security scan...")

    try:
        # Offload blocking subprocess calls to a thread
        def perform_scan():
            # Run Lynis
            lynis_result = subprocess.run(
                "sudo lynis audit system", shell=True, capture_output=True, text=True
            ).stdout

            # Run chkrootkit
            chkrootkit_result = subprocess.run(
                "sudo chkrootkit", shell=True, capture_output=True, text=True
            ).stdout

            # Run Rkhunter
            rkhunter_result = subprocess.run(
                "sudo rkhunter --check --skip-keypress", shell=True, capture_output=True, text=True
            ).stdout

            return (
                f"=== Lynis Report ===\n{lynis_result}\n"
                f"=== Chkrootkit Report ===\n{chkrootkit_result}\n"
                f"=== Rkhunter Report ===\n{rkhunter_result}"
            )

        # Offload to thread pool
        scan_result = await asyncio.to_thread(perform_scan)

        # Save to file if result is too long
        if len(scan_result) > 4000:
            with open("security_scan_report.txt", "w") as file:
                file.write(scan_result)

            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document="security_scan_report.txt",
                caption="Security scan completed. See attached report."
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=scan_result
            )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Error during security scan: {e}"
        )

async def perform_security_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scan_result = await run_security_scan()
    await context.bot.send_message(f"Security Scan Results:\n{scan_result}")



# Function to check the status of services
async def server_health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the services from the user's message or use default ones
    services_to_check = default_services
    if context.args:
        services_to_check = context.args

    # Check the status of each service
    health_report = []
    for service in services_to_check:
        try:
            result = subprocess.run(
                ["/usr/bin/systemctl", "is-active", service],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            service_status = result.stdout.decode().strip()

            if service_status == "active":
                health_report.append(f"<b>{service}</b> is <b>running</b>.")
            else:
                health_report.append(f"<b>{service}</b> is <b>NOT running</b>!")
        except Exception as e:
            health_report.append(f"<b>{service}</b> check failed: {str(e)}")

    # Send the health status to the user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="\n".join(health_report),
        parse_mode="HTML",
    )

async def check_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await server_health_check(update, context)
    else:
        await update.message.reply_text(
            "Please specify one or more services to check (e.g., /check_services apache2 mysql)"
        )
        await update.message.reply_text(
            "Common services: apache2, nginx, mysql, redis, postgresql."
        )


# Function to allow the admin to set the list of services to monitor
async def set_monitored_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == admin_id:
        if context.args:
            global default_services
            default_services = context.args
            await update.message.reply_text(
                f"Monitored services updated: {', '.join(default_services)}"
            )
        else:
            await update.message.reply_text(
                "Please provide a list of services to monitor, separated by spaces (e.g., /set_monitored_services apache2 nginx mysql)."
            )
    else:
        await update.message.reply_text(
            "You are not authorized to perform this action."
        )

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = {
        "CPU Usage": f"{get_cpu_usage()}%",
        "Memory Usage": get_memory_usage(),
        "Disk Usage": get_disk_usage(),
        "Firewall Status": firewall_status(),
    }
    report_text = (
        f"System Status Report:\n"
        f"CPU Usage: {report['CPU Usage']}\n"
        f"Memory Usage: {report['Memory Usage']}\n"
        f"Disk Usage: {report['Disk Usage']}\n"
        f"Firewall Status:\n{report['Firewall Status']}"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=report_text)


async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu_usage = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage()

    # Form the complete message by concatenating all usage stats.
    message = (
        f"Нагрузка на процессор составляет {cpu_usage}%\n"
        f"Памяти использовано:\n"
        f"Всего: {memory['total']}, Занято: {memory['used']}, "
        f"Доступно: {memory['available']}, {memory['percent']}%\n"
        f"Емкость диска:\n"
        f"Всего: {disk['total']}, Заполнено: {disk['used']}, "
        f"Доступно: {disk['free']}, {disk['percent']}%"
    )

    # Send the composed message.
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    await update.message.reply_text(
        f"Memory Usage:\nTotal: {memory['total']}, Used: {memory['used']}, "
        f"Available: {memory['available']}, Usage: {memory['percent']}%"
    )


async def monitor_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor disk usage."""
    disk = get_disk_usage()
    await update.message.reply_text(
        f"Disk Usage:\nTotal: {disk['total']}, Used: {disk['used']}, "
        f"Free: {disk['free']}, Usage: {disk['percent']}%"
    )


async def send_alert_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends an alert to the admin."""
    await context.bot.send_message(
        chat_id=admin_id, text="Alert: Critical issue detected."
    )

async def select_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_buttons = [
        [InlineKeyboardButton("👽 Nmap сканер", callback_data="run_nmap_scan")],
        [InlineKeyboardButton("🥷 Nikto сканер", callback_data="run_nikto_scan")],
        [InlineKeyboardButton("👽 Системный", callback_data="run_security_scan")],
        [InlineKeyboardButton("🥷 Интерактивный", callback_data="interactive_scan")],
        [InlineKeyboardButton("🖇 Ввести команду вручную", callback_data="input_command_run")],
        [InlineKeyboardButton("⬅ Назад", callback_data="tasks_autoset")],
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите задачу для запуска:",
        reply_markup=InlineKeyboardMarkup(task_buttons),
    )


async def input_command_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_command = update.message.text  # Use message text instead of query
    try:
        process = await asyncio.create_subprocess_shell(
            user_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = (
            stdout.decode() if process.returncode == 0 else f"Error: {stderr.decode()}"
        )
    except Exception as e:
        result = f"Error running command: {e}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)


# Server IP Retrieval
async def get_server_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve server's public and private IP addresses."""
    try:
        hostname = socket.gethostname()
        private_ip = socket.gethostbyname(hostname)
        public_ip = requests.get("https://api.ipify.org").text
        result = f"Private IP: {private_ip}\nPublic IP: {public_ip}"
    except Exception as e:
        logger.error(f"Error getting IPs: {e}")
        result = f"Error: {str(e)}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)


# Ping Host
async def ping_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ping a host to check if it's reachable."""
    host = context.args[0] if context.args else "kalinux.org.ru"
    try:
        process = await asyncio.create_subprocess_shell(
            f"/usr/bin/ping -c 1 {host}", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = (
            f"{host} is reachable."
            if process.returncode == 0
            else f"{host} is not reachable.\n{stderr.decode()}"
        )
    except Exception as e:
        result = f"Error pinging host: {e}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)


async def handle_long_output(output, filename, update, context, max_length=4096):
    """Handle long outputs by splitting or sending as a file."""
    if len(output) <= max_length:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=output)
    else:
        await send_output_as_file(
            filename=filename, content=output, update=update, context=context
        )

async def get_socket_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get network socket status using `ss` command."""
    try:
        process = await asyncio.create_subprocess_shell(
            "/usr/bin/ss -tulnap", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        scan_result = stdout.decode()

        if process.returncode == 0 and len(scan_result) > 4000:
         with open("socket_status.txt", "w") as file:
            file.write(scan_result)

         await context.bot.send_document(
           chat_id=update.effective_chat.id,
           document="socket_status.txt",
           caption="Scan completed. See attached report."
        )
        elif process.returncode == 0 and len(scan_result) < 4000:
         await context.bot.send_message(chat_id=update.effective_chat.id, text=scan_result)

        else:
            result = stdout.decode()
            await handle_long_output(
               output=result,
               filename="socket_status.txt",
               update=update,
               context=context
         )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Error running ss command: {e}"
        )



# Run `netstat` command
async def get_netstat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve network statistics using `netstat`."""
    try:
        process = await asyncio.create_subprocess_shell(
            "/usr/bin/netstat -tuln", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = (
            stdout.decode() if process.returncode == 0 else f"Error: {stderr.decode()}"
        )
    except Exception as e:
        result = f"Error running netstat: {e}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)


# Run `nikto` scan
async def run_nikto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run `nikto` scan on a target."""
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please specify a target for the scan {target})."
        )
        return

    target = context.args[0]
    try:
        process = await asyncio.create_subprocess_shell(
            f"/usr/bin/nikto -h {target}", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = (
            stdout.decode() if process.returncode == 0 else f"Error: {stderr.decode()}"
        )
    except Exception as e:
        result = f"Error running nikto: {e}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)


async def run_nmap_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run nmap scan on a target."""
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please specify a target for the scan (e.g., `/nmap <target>`)."
        )
        return

    target = context.args[0]
    try:
        process = await asyncio.create_subprocess_shell(
            f"/usr/bin/nmap -sF -A {target}", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = (
            stdout.decode() if process.returncode == 0 else f"Error: {stderr.decode()}"
        )
        logger.info(f"Nmap Scan Result: {result}")  # Add this log to view the result
    except Exception as e:
        result = f"Error running nmap: {e}"
        logger.error(f"Error running nmap: {e}")

    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)


async def interactive_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provide an interactive prompt for scanning options."""
    target = context.args[0] if context.args else "localhost"
    scan_type = context.args[1] if len(context.args) > 1 else "nmap"


def firewall_status(sellf, command):
    try:
        result = subprocess.run(
            ["sudo", "iptables", "-L", "-v", "-n", "--line-numbers"],
            capture_output=True,
            text=True,
        )
        return (
            result.stdout if result.returncode == 0 else "Firewall status unavailable."
        )
    except Exception as e:
        logging.error(f"Error checking firewall: {e}")
        return f"Error: {str(e)}"

# ========== System Monitoring Utilities ==========


# Function to display system information
async def system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = time.time() - psutil.boot_time()
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))

    system_info_text = (
        f"<b>System Information:</b>\n"
        f"<b>CPU Usage:</b> {cpu_usage}%\n"
        f"<b>Memory Usage:</b> {memory.percent}% ({memory.available / (1024 * 1024):.2f} MB free)\n"
        f"<b>Disk Usage:</b> {disk.percent}% ({disk.free / (1024 * 1024):.2f} MB free)\n"
        f"<b>Uptime:</b> {uptime_str}"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=system_info_text, parse_mode="HTML"
    )


# Function to trigger disk cleanup
async def disk_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    temp_dir = "/home/kalinux/kalis/temp"  # Example temp directory
    logs_dir = "/home/kalinux/kalis/logs/logstodelete"  # Example logs directory
    cleanup_logs = []

    for directory in [temp_dir, logs_dir]:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleanup_logs.append(f"Deleted {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        cleanup_logs.append(f"Deleted directory {file_path}")
                except Exception as e:
                    cleanup_logs.append(f"Failed to delete {file_path}: {e}")
        else:
            cleanup_logs.append(f"Directory {directory} does not exist.")

    cleanup_report = "\n".join(cleanup_logs) if cleanup_logs else "No files to clean."
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>Disk Cleanup Complete:</b>\n{cleanup_report}",
        parse_mode="HTML",
    )


# Function to restart the bot
async def restart_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bot is restarting..."
    )
    os.execv(sys.executable, ["systemctl restart bot"] + sys.argv)

async def check_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await server_health_check(update, context)
    else:
        await update.message.reply_text(
            "Please specify one or more services to check (e.g., /check_services apache2 mysql)"
        )
        await update.message.reply_text(
            "Common services: apache2, nginx, mysql, redis, postgresql."
        )


# Function to allow the admin to set the list of services to monitor
async def set_monitored_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == admin_id:
        if context.args:
            global default_services
            default_services = context.args
            await update.message.reply_text(
                f"Monitored services updated: {', '.join(default_services)}"
            )
        else:
            await update.message.reply_text(
                "Please provide a list of services to monitor, separated by spaces (e.g., /set_monitored_services apache2 nginx mysql)."
            )
    else:
        await update.message.reply_text(
            "You are not authorized to perform this action."
        )

# ========== Bot Setup ==========

if __name__ == "__main__":
    bot_app = ApplicationBuilder().token(TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("interactive_scan", interactive_scan))
    bot_app.add_handler(CommandHandler("monitor", monitor))
    bot_app.add_handler(CommandHandler("monitor_cpu", monitor_cpu))
    bot_app.add_handler(CommandHandler("monitor_memory", monitor_memory))
    bot_app.add_handler(CommandHandler("monitor_disk", monitor_disk))
    bot_app.add_handler(CommandHandler("security_scan", perform_security_scan))
    bot_app.add_handler(CommandHandler("info", info))
    bot_app.add_handler(CommandHandler("help_command", help_command))
    bot_app.add_handler(CommandHandler("enter_token", enter_token))
    bot_app.add_handler(CommandHandler("check_services", check_services))
    bot_app.add_handler(CommandHandler("server_management_menu", server_management_menu))
    bot_app.add_handler(CommandHandler("set_monitored_services", set_monitored_services))
    bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_token_input))
    bot_app.add_handler(CallbackQueryHandler(button))
    bot_app.add_handler(CommandHandler("sysinfo_task", sysinfo_task))

    bot_app.add_error_handler(error_handler)

    bot_app.run_polling()


# Инициализация приложения Telegram
def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()


if __name__ == "__main__":
    main()
