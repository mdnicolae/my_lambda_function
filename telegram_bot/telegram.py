import helper
import requests

# Retrieve the Telegram token from Secrets Manager
secret_name = "telegram/bot_token"
secrets = helper.get_secret(secret_name)
TELEGRAM_TOKEN = secrets.get('TELEGRAM_TOKEN') if secrets else None
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/" if TELEGRAM_TOKEN else None


def send_message(chat_id, text):
    url = TELEGRAM_API_URL + "sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending message: {e}")
