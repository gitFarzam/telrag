import requests
import logging
import os

from django.conf import settings

import chat.constants as constants

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# 

# https://api.telegram.org/bot8536509873:BAFG4ILMA39Iuhj8SQhy6hks5RspmDRs_6D/deleteWebhook

telegram_api_key = os.getenv('TELEGRAM_API_KEY')
if settings.DEBUG:
    telegram_api_key = os.getenv('TELEGRAM_DEV_API_KEY')


def set_telegram_webhook_secret():

    # Deleting the current webhook
    url = f"https://api.telegram.org/bot{telegram_api_key}/setWebhook"
    response = requests.post(url)
    print("Deleting webhook status: ",response.content, response.status_code)

    tg_secret_key = os.getenv('TELEGRAM_WEBHOOK_SECRET')

    address = os.getenv('ONLINE_WEBHOOK_ADDRESS')
    if settings.DEBUG:
        tg_secret_key = os.getenv('TELEGRAM_DEV_WEBHOOK_SECRET')
        address = os.getenv('DEV_WEBHOOK_ADDRESS')
    
    url = f"https://api.telegram.org/bot{telegram_api_key}/setWebhook?url={address}&secret_token={tg_secret_key}"
    response = requests.post(url)
    print(f"Setting New Webhook on: {address}",response.content, response.status_code)


def info_telegram_webhook():
    url = f"https://api.telegram.org/bot{telegram_api_key}/getUpdates"
    response = requests.post(url)
    print(f"Response content: {response.content}")


def delete_telegram_webhook():
    url = f"https://api.telegram.org/bot{telegram_api_key}/deleteWebhook"
    response = requests.post(url)
    print(f"Response content: {response.content}")


def send_message(chat_id, text=None,document_id=None,reply_to_message_id=None,command=False):
    url = f"https://api.telegram.org/bot{telegram_api_key}/sendMessage"

    reply_markup = {}
    if document_id:
        reply_markup = document_markup_for_telegram(document_id)

    payload = {
        "chat_id": chat_id,
        "text": text,
        "message_id" : 5 ,
        "parse_mode": "HTML",
        "reply_markup" : reply_markup,
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    response = requests.post(url, json=payload)
    response_dict:dict = response.json()

    if not command:
        # when there is a command, telegram doesnt send back a message id, so I can not get anything!
        result:dict = response_dict.get('result',{})
        telegram_message_id = result.get('message_id',{})
        return telegram_message_id
    
    return None


def document_markup_for_telegram(document_id:int):
    return {
        "inline_keyboard": [
            [
                { "text": "❌ Delete", "callback_data": str(document_id) },
            ],
        ]
    }




def telegram_message_parser(json_data_dict:dict):

    parsed_data = {'metadata':{} , 'data':{}}
    message = json_data_dict.get('message',None)
    callback_query = json_data_dict.get('callback_query',None)

    if message:
        # print('message data: ',message)
        message_keys = message.keys()
        # print('message keys: ', message_keys)

        parsed_data['metadata']['chat_id'] = message.get('from',{}).get('id')
        parsed_data['metadata']['message_id'] = message.get('message_id',{})
        parsed_data['type'] = "new" # new | reply | command

        if 'reply_to_message' in message_keys:
            parsed_data['metadata']['reply_message_id'] = message['reply_to_message']['message_id']
            parsed_data['type'] = "reply" # new | reply | command 

        if 'caption' in message_keys :
            parsed_data['metadata']['caption'] = message.get('caption')

        if 'text' in message_keys :
            parsed_data['data']['text'] = message.get('text')

        if 'photo' in message_keys :
            parsed_data['data']['photo'] = message.get('photo')

        if 'voice' in message_keys :
            parsed_data['data']['voice'] = message.get('voice')

        if 'entities' in message_keys:
            parsed_data['type'] = "entities"
            parsed_data['data']['entities'] = message.get('entities')

    
    if callback_query:
        parsed_data['type'] = "button"
        parsed_data['metadata']['chat_id'] = callback_query.get('from',{}).get('id')
        parsed_data['metadata']['message_id'] = callback_query.get('message_id',{})
    # Callback Query
        document_id = json_data_dict.get('callback_query',None).get('data',{})
        if document_id:
                parsed_data['data']['del_document_id'] = document_id

    return parsed_data



def telegram_downloader(file_id):

    # Step 1: get file_path
    url = f"https://api.telegram.org/bot{telegram_api_key}/getFile"
    payload = {"file_id" : file_id}
    response = requests.get(url,params=payload)
    file_path = response.json()["result"]["file_path"]

    # Step 2: download file
    file_url = f"https://api.telegram.org/file/bot{telegram_api_key}/{file_path}"
    file_data = requests.get(file_url).content

    with open(constants.VOICE_PATH_TEMP/"temp.oga", "wb") as f:
        f.write(file_data)


    return file_data