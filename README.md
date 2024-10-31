# 🤖 Dawn Auto Reward Bot

An automated bot for managing Dawn rewards with Telegram integration and proxy support.

## ✨ Features

- 🔄 Multi-token support
- 🌐 Proxy mode for distributed access
- 📱 Telegram notifications
- ⚡ Automatic keepalive and point tracking
- 🔐 Secure token management
- 📊 Detailed logging system

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Required packages (install via pip):
  ```bash
  pip install -r requirements.txt
  ``` 
  or
  ```bash
  python -m pip install -r requirements.txt --user
  ```

### How to get telegram token and chat id

- https://core.telegram.org/bots/tutorial#getting-ready (Create telegram bot and get telegram token)
- https://t.me/chatIDrobot (get chat id)

### How to get Dawn token
1. Download extension: [Here](https://chromewebstore.google.com/detail/dawn-validator-chrome-ext/fpdkjdnhkakefebpekbdhillbhonfjjp?authuser=0&hl=en)
2. Open Dawn, Register and Login
3. Use this code `edjxbpnx`
4. Right click on mouse and select `inspect`
5. Select `Network` tab
6. Click On `Boost Rewards` then back again
7. In devtools filter find `getpoint` click on it
8. Scroll down and find `Authorization` and copy the value only token 22xx not using `Bearer`

### 🔧 Configuration

1. Rename `.env.example` to `.env` and fill in the following variables:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   CHAT_ID=your_telegram_chat_id
   PROXY_MODE=true/false
   MULTI_TOKEN=true/false
   TELEGRAM_MODE=true/false
   ```

2. If using multiple tokens, create `token.txt`:
   ```
   token1
   token2
   ...
   ```

3. If using proxies, create `proxy.txt`:
   ```
   proxy1
   proxy2
   ...
   ```
   format example if using authentication proxy:
   - http://ip:port@username:password (worked)
   - socks5://ip:port@username:password (not tested)

   also working with unauthenticated proxy `ip:port`

## 🎮 Usage

Run the bot: 
```bash
python app.py
```
## 🛎️ Telegram
Join my telegram channel: https://t.me/tdropid

## 📄 License

This project is open source and available under the MIT License.