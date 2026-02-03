# telegram_app/telegram.py
import requests
from dotenv import load_dotenv
import os
load_dotenv()

# https://api.telegram.org/bot8536509873:BAFG4ILMA39Iuhj8SQhy6hks5RspmDRs_6D/getUpdates

# https://api.telegram.org/bot8536509873:BAFG4ILMA39Iuhj8SQhy6hks5RspmDRs_6D/deleteWebhook


def send_message(chat_id=None, text=None):
    chat_id = 120358726
    text = "Baba khoobe?"
    telegram_api_key = os.getenv('telegram_api')
    url = f"https://api.telegram.org/bot{telegram_api_key}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    requests.post(url, json=payload)



if __name__ == "__main__":
    send_message()