import requests
import time
import urllib3
import os
import logging
import asyncio
from dotenv import load_dotenv
from logger import TelegramLogger, setup_logger
from colorama import Fore, Style, init
from datetime import datetime, timedelta
import random
from urllib.parse import urlparse
import platform
import sys

init(autoreset=True)

# Ignore InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write("# This file contains environment variables.\n")

load_dotenv()

class Emoji:
    CHECK = "✅"
    ERROR = "❌"
    ROCKET = "🚀"
    CHART = "📊"
    PING = "📡"
    GEAR = "⚙️"
    CLOCK = "🕒"
    INFO = "ℹ️"
    WARNING = "⚠️"
    ROBOT = "🤖"

def prompt_for_env_variables():
    inputs = []

    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        telegram_token = input("Please enter your Telegram Bot Token: ")
        inputs.append(f"TELEGRAM_TOKEN={telegram_token}")

    chat_id = os.getenv("CHAT_ID")
    if not chat_id:
        chat_id = input("Please enter your Chat ID: ")
        inputs.append(f"CHAT_ID={chat_id}")

    proxy_mode = os.getenv("PROXY_MODE")
    if not proxy_mode:
        proxy_mode = input("Enable proxy mode? (true/false): ").lower()
        inputs.append(f"PROXY_MODE={proxy_mode}")

    multi_token = os.getenv("MULTI_TOKEN")
    if not multi_token:
        multi_token = input("Enable multi-token mode? (true/false): ").lower()
        inputs.append(f"MULTI_TOKEN={multi_token}")

    telegram_mode = os.getenv("TELEGRAM_MODE")
    if not telegram_mode:
        telegram_mode = input("Enable telegram notifications? (true/false): ").lower()
        inputs.append(f"TELEGRAM_MODE={telegram_mode}")

    with open('.env', 'a') as f:
        for item in inputs:
            f.write(f"{item}\n")

    return telegram_token, chat_id, proxy_mode.lower() == 'true', multi_token.lower() == 'true', telegram_mode.lower() == 'true'

def load_tokens(multi_token_mode):
    tokens = []
    try:
        with open('token.txt', 'r') as f:
            tokens = [line.strip() for line in f if line.strip()]
        
        if not tokens:
            raise FileNotFoundError
        
        if not multi_token_mode:
            tokens = [tokens[0]]  # Only use first token in single token mode
            logging.info(f"{Fore.YELLOW}Single token mode: Using only the first token")
        
    except FileNotFoundError:
        print("token.txt not found or empty. Please enter token:")
        token = input("Enter Dawn Token: ")
        tokens.append(token)
        
        with open('token.txt', 'w') as f:
            f.write(f"{token}\n")
    
    return tokens

def load_proxies(proxy_mode):
    if not proxy_mode:
        logging.info(f"{Fore.YELLOW}Proxy mode disabled")
        return []
        
    proxies = []
    try:
        with open('proxy.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        if not proxies:
            logging.info("No proxies found in proxy.txt, will use direct connection")
    except FileNotFoundError:
        logging.info("proxy.txt not found, will use direct connection")
    
    return proxies

# Load configuration
TELEGRAM_TOKEN, CHAT_ID, PROXY_MODE, MULTI_TOKEN, TELEGRAM_MODE = prompt_for_env_variables()
TOKENS = load_tokens(MULTI_TOKEN)
PROXIES = load_proxies(PROXY_MODE)

# Create proxy pool only if proxy mode is enabled
if PROXY_MODE:
    PROXY_POOL = PROXIES if PROXIES else [None] * len(TOKENS)
    if len(PROXY_POOL) < len(TOKENS):
        PROXY_POOL = PROXY_POOL * (len(TOKENS) // len(PROXY_POOL) + 1)
    PROXY_POOL = PROXY_POOL[:len(TOKENS)]
else:
    PROXY_POOL = [None] * len(TOKENS)

telegram_logger = TelegramLogger(TELEGRAM_TOKEN, CHAT_ID, TELEGRAM_MODE)
setup_logger(telegram_logger)

POINTS_URL = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
PING_URL = "https://www.aeropres.in/dawnserver/ping"
KEEPALIVE_URL = "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive"

def create_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }

email = ""

# Function to fetch points
async def fetch_points(headers, proxy=None):
    global email
    try:
        session = requests.Session()
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
        session.verify = False
        response = session.get(POINTS_URL, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", {}).get("rewardPoint", {})
        email = data.get('userId','')

        total_points = sum([
            data.get('points', 0),
            data.get('twitter_x_id_points', 0),
            data.get('discordid_points', 0),
            data.get('telegramid_points', 0)
        ])

        telegram_message = (
            f"{Emoji.CHART} *Account Details*\n\n"
            f"└─ ID: `{data.get('_id')}`\n"
            f"└─ User: `{email}`\n"
            f"└─ Points: `{total_points}`\n"
        )

        logging.info(f"{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Fetching points...\n{Fore.YELLOW}{telegram_message}")
        await telegram_logger.send_message(telegram_message)
        return total_points

    except requests.exceptions.RequestException as e:
        error_msg = f"{Emoji.ERROR} *Error Fetching Points*\n└─ Error: `{str(e)}`"
        logging.error(f"{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}")
        await telegram_logger.send_message(error_msg)
        return 0

async def ping_server(headers, proxy=None):
    try:
        session = requests.Session()
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
        session.verify = False
        response = session.get(PING_URL, headers=headers)
        response.raise_for_status()
        success_msg = f"{Emoji.PING} *Ping Status*\n└─ Status: `Successful`\n└─ Response: `{response.text}`"
        logging.info(f"{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {success_msg}")
        await telegram_logger.send_message(success_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"{Emoji.ERROR} *Ping Failed*\n└─ Error: `{str(e)}`"
        logging.error(f"{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}")
        await telegram_logger.send_message(error_msg)

async def keep_alive(headers, last_keepalive_log_time, proxy=None):
    try:
        session = requests.Session()
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
        session.verify = False
        response = session.post(KEEPALIVE_URL, headers=headers, json={
            "username": email,
            "extensionid": "fpdkjdnhkakefebpekbdhillbhonfjjp",
            "numberoftabs": 0,
            "_v": "1.0.9"
        }, timeout=30)

        if response.status_code == 200:
            success_msg = f"{Emoji.CHECK} *Keepalive Status*\n└─ Status: `Successful`"
            logging.info(f"{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Keepalive successful.")
            current_time = datetime.now()
            if current_time - last_keepalive_log_time >= timedelta(minutes=5):
                await telegram_logger.send_message(success_msg)
                last_keepalive_log_time = current_time
        else:
            warning_msg = f"{Emoji.WARNING} *Keepalive Warning*\n└─ Status Code: `{response.status_code}`"
            logging.warning(f"{Fore.YELLOW}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {warning_msg}")
            await telegram_logger.send_message(warning_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"{Emoji.ERROR} *Keepalive Failed*\n└─ Error: `{str(e)}`"
        logging.error(f"{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}")
        await telegram_logger.send_message(error_msg)

# Main execution flow
async def main():
    logging.basicConfig(level=logging.INFO)
    headers_list = [create_headers(token) for token in TOKENS]
    last_keepalive_log_times = [datetime.now() - timedelta(minutes=5) for _ in TOKENS]

    # Log configuration
    config_msg = (
        f"{Emoji.ROBOT} *Dawn Auto Reward Bot Started*\n\n"
        f"{Emoji.GEAR} *Configuration*\n"
        f"└─ Multi-token: `{'Enabled' if MULTI_TOKEN else 'Disabled'}`\n"
        f"└─ Proxy mode: `{'Enabled' if PROXY_MODE else 'Disabled'}`\n"
        f"└─ Telegram mode: `{'Enabled' if TELEGRAM_MODE else 'Disabled'}`\n"
        f"└─ Active tokens: `{len(TOKENS)}`\n"
    )
    if PROXY_MODE:
        config_msg += f"└─ Active proxies: `{len(PROXIES)}`\n"

    logging.info(f"\n{Fore.CYAN}{config_msg}{Style.RESET_ALL}")
    if TELEGRAM_MODE:
        await telegram_logger.send_message(config_msg)

    while True:
        for i, (headers, proxy) in enumerate(zip(headers_list, PROXY_POOL)):
            try:
                proxy_info = f"with proxy: {proxy}" if proxy and PROXY_MODE else "without proxy"
                account_msg = f"{Emoji.INFO} *Processing Account*\n└─ Account: `{i+1}/{len(TOKENS)}`\n└─ Proxy: `{proxy_info}`"
                logging.info(f"\n{Fore.CYAN}{account_msg}{Style.RESET_ALL}")
                await telegram_logger.send_message(account_msg)
                
                await ping_server(headers, proxy if PROXY_MODE else None)
                await keep_alive(headers, last_keepalive_log_times[i], proxy if PROXY_MODE else None)
                await fetch_points(headers, proxy if PROXY_MODE else None)
                await asyncio.sleep(5)
            except Exception as e:
                error_msg = f"{Emoji.ERROR} *Error Processing Account*\n└─ Account: `{i+1}`\n└─ Error: `{str(e)}`"
                logging.error(error_msg)
                await telegram_logger.send_message(error_msg)
        
        await asyncio.sleep(500)

def print_banner():
    os_info = platform.system()
    python_version = sys.version.split()[0]
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    banner = f"""
{Fore.CYAN}================================================
                Dawn Auto Reward Bot                
================================================

{Emoji.ROBOT} Version    : 1.0.0
{Emoji.GEAR} OS         : {os_info}
{Emoji.INFO} Python     : {python_version}
{Emoji.CLOCK} Time       : {current_time}

================================================
                 Developer Info                 
================================================

{Emoji.ROCKET} Github     : https://github.com/tnodes
{Emoji.CHART} Telegram   : https://t.me/tdropid

================================================{Style.RESET_ALL}

{Fore.YELLOW}[!] Make sure you have configured your .env file correctly
[!] If you're using proxy mode, check your proxy.txt
[!] Ensure your token.txt contains valid tokens{Style.RESET_ALL}
"""
    print(banner)

if __name__ == "__main__":
    print_banner()
    asyncio.run(main())