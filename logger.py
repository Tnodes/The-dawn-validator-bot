import logging
import asyncio
import aiohttp

class TelegramLogger:
    def __init__(self, token, chat_id, enabled=True):
        self.token = token
        self.chat_id = chat_id
        self.enabled = enabled

    async def send_message(self, message):
        if not self.enabled:
            return
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logging.error(f"Failed to send message to Telegram. Status: {response.status}, Response: {await response.text()}")
                    else:
                        return await response.json()
        
        except aiohttp.ClientError as e:
            logging.error(f"Network error while sending message to Telegram: {str(e)}")
        
        except Exception as e:
            logging.error(f"Unexpected error while sending message to Telegram: {str(e)}")

    def start(self):
        pass

def setup_logger(telegram_logger):
    logger = logging.getLogger()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')  # Simplified format
    console_handler.setFormatter(console_formatter)

    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        logger.addHandler(console_handler)

    class TelegramHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR and telegram_logger.enabled: 
                msg = self.format(record)
                loop = asyncio.get_event_loop()
                loop.create_task(telegram_logger.send_message(msg))  

    telegram_handler = TelegramHandler()
    telegram_handler.setLevel(logging.ERROR) 
    logger.addHandler(telegram_handler)

    logger.setLevel(logging.DEBUG)
