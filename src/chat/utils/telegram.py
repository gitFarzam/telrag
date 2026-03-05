# telegram_app/telegram.py
import requests
from dotenv import load_dotenv
import os
import json
load_dotenv()

# https://api.telegram.org/bot8536509873:BAFG4ILMA39Iuhj8SQhy6hks5RspmDRs_6D/getUpdates

# https://api.telegram.org/bot8536509873:BAFG4ILMA39Iuhj8SQhy6hks5RspmDRs_6D/deleteWebhook
telegram_api_key = os.getenv('telegram_api')


def set_telegram_webhook_secret():
    tg_secret_key = os.getenv('TELEGRAM_WEBHOOK_SECRET')
    url_host = "https://<your-ngrok-subdomain>.ngrok-free.dev/webhook/"
    url = f"https://api.telegram.org/bot{telegram_api_key}/setWebhook?url={url_host}&secret_token={tg_secret_key}"
    """
    in case a domain (url) is also required

    https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://yourserver.com/hook&secret_token=YOUR_SECRET_STRING
    
    """
    response = requests.post(url)
    print(response.content, response.status_code)

# set_telegram_webhook_secret()

def send_message(chat_id=120358726, text=None,document_id=None,reply_to_message_id=None,command=False):
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

    if not command:
        # when there is a command, telegram doesnt send back a message id, so I can not get anything!
        telegram_message_id = response.json()['result']['message_id']
        """
            {'ok': True, 'result': {'message_id': 34, 'from': {'id': 8176918185, 'is_bot': True, 'first_name': 'telrag', 'username': 'telrag_bot'}, 'chat': {'id': 120358726, 'first_name': 'F', 'username': 'Farzam91', 'type': 'private'}, 'date': 1770237370, 'text': 'Hey! Somebody have a question:\nU'}}
        """

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

    {'type' :'new|reply|entities|button','metadata': {'chat_id': 120358726}, 'data': {'text': 'Farzam is a good boy'}}

    
    {'update_id': 472344065, 'message': {'message_id': 221, 'from': {'id': 120358726, 'is_bot': False, 'first_name': 'F', 'username': 'Farzam91', 'language_code': 'en'}, 'chat': {'id': 120358726, 'first_name': 'F', 'username': 'Farzam91', 'type': 'private'}, 'date': 1771890593, 'text': 'This is /com1 this is /com2', 'entities': [{'offset': 8, 'length': 5, 'type': 'bot_command'}, {'offset': 22, 'length': 5, 'type': 'bot_command'}]}}

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

    with open("sample.oga", "wb") as f:
        f.write(file_data)


    return file_data


"""
pdf

{'message': {'caption': 'park oregon credential',
             'chat': {'first_name': 'F',
                      'id': 120358726,
                      'type': 'private',
                      'username': 'Farzam91'},
             'date': 1770255791,
             'document': {'file_id': 'BQACAgQAAxkBAAMsaYP1ry0zMIMGCwncT-gbtf-nM4sAAnUbAAIfzSBQCzUaaWgJFKQ4BA',
                          'file_name': 'oregon_state_park.pdf',
                          'file_size': 142236,
                          'file_unique_id': 'AgADdRsAAh_NIFA',
                          'mime_type': 'application/pdf',
                          'thumb': {'file_id': 'AAMCBAADGQEAAyxpg_WvLTMwgwYLCdxP6Bu1_6cziwACdRsAAh_NIFALNRppaAkUpAEAB20AAzgE',
                                    'file_size': 8763,
                                    'file_unique_id': 'AQADdRsAAh_NIFBy',
                                    'height': 320,
                                    'width': 247},
                          'thumbnail': {'file_id': 'AAMCBAADGQEAAyxpg_WvLTMwgwYLCdxP6Bu1_6cziwACdRsAAh_NIFALNRppaAkUpAEAB20AAzgE',
                                        'file_size': 8763,
                                        'file_unique_id': 'AQADdRsAAh_NIFBy',
                                        'height': 320,
                                        'width': 247}},
             'from': {'first_name': 'F',
                      'id': 120358726,
                      'is_bot': False,
                      'language_code': 'en',
                      'username': 'Farzam91'},
             'message_id': 44},
 'update_id': 472343944}

"""




"""
photo
{'message': {'chat': {'first_name': 'F',
                      'id': 120358726,
                      'type': 'private',
                      'username': 'Farzam91'},
             'date': 1770243508,
             'from': {'first_name': 'F',
                      'id': 120358726,
                      'is_bot': False,
                      'language_code': 'en',
                      'username': 'Farzam91'},
             'message_id': 41,
             'photo': [{'file_id': 'AgACAgQAAxkBAAMpaYPFtDc1p22RPYTB_z3sWMziAAGXAALmEWsbH80YUD4fr2mvsd1gAQADAgADcwADOAQ',
                        'file_size': 2176,
                        'file_unique_id': 'AQAD5hFrGx_NGFB4',
                        'height': 90,
                        'width': 67},
                       {'file_id': 'AgACAgQAAxkBAAMpaYPFtDc1p22RPYTB_z3sWMziAAGXAALmEWsbH80YUD4fr2mvsd1gAQADAgADbQADOAQ',
                        'file_size': 28571,
                        'file_unique_id': 'AQAD5hFrGx_NGFBy',
                        'height': 320,
                        'width': 240},
                       {'file_id': 'AgACAgQAAxkBAAMpaYPFtDc1p22RPYTB_z3sWMziAAGXAALmEWsbH80YUD4fr2mvsd1gAQADAgADeAADOAQ',
                        'file_size': 113169,
                        'file_unique_id': 'AQAD5hFrGx_NGFB9',
                        'height': 800,
                        'width': 600},
                       {'file_id': 'AgACAgQAAxkBAAMpaYPFtDc1p22RPYTB_z3sWMziAAGXAALmEWsbH80YUD4fr2mvsd1gAQADAgADeQADOAQ',
                        'file_size': 144107,
                        'file_unique_id': 'AQAD5hFrGx_NGFB-',
                        'height': 1280,
                        'width': 960}]},
 'update_id': 472343941}

"""



"""
audio
{'message': {'chat': {'first_name': 'F',
                      'id': 120358726,
                      'type': 'private',
                      'username': 'Farzam91'},
             'date': 1770243560,
             'from': {'first_name': 'F',
                      'id': 120358726,
                      'is_bot': False,
                      'language_code': 'en',
                      'username': 'Farzam91'},
             'message_id': 42,
             'voice': {'duration': 3,
                       'file_id': 'AwACAgQAAxkBAAMqaYPF6Lea0J-Ne01ibzMYjtsDX18AAhIdAAIfzRhQcXMUKc0ksks4BA',
                       'file_size': 13127,
                       'file_unique_id': 'AgADEh0AAh_NGFA',
                       'mime_type': 'audio/ogg'}},

"""



"""
with reply
{'message': {'chat': {'first_name': 'F',
                      'id': 120358726,
                      'type': 'private',
                      'username': 'Farzam91'},
             'date': 1770235893,
             'from': {'first_name': 'F',
                      'id': 120358726,
                      'is_bot': False,
                      'language_code': 'en',
                      'username': 'Farzam91'},
             'message_id': 28,
             'reply_to_message': {'chat': {'first_name': 'F',
                                           'id': 120358726,
                                           'type': 'private',
                                           'username': 'Farzam91'},
                                  'date': 1770235357,
                                  'from': {'first_name': 'telrag',
                                           'id': 8176918185,
                                           'is_bot': True,
                                           'username': 'telrag_bot'},
                                  'message_id': 26,
                                  'text': 'Hey! Somebody have a question:\nhi'},
             'text': 'Wait'},
 'update_id': 472343936}
    """

"""
without reply
{'message': {'chat': {'first_name': 'F',
                      'id': 120358726,
                      'type': 'private',
                      'username': 'Farzam91'},
             'date': 1770243368,
             'from': {'first_name': 'F',
                      'id': 120358726,
                      'is_bot': False,
                      'language_code': 'en',
                      'username': 'Farzam91'},
             'message_id': 40,
             'text': 'Gooz'},
'update_id': 472343940}
    
"""


"""
telegram command

{'update_id': 472344065, 'message': {'message_id': 221, 'from': {'id': 120358726, 'is_bot': False, 'first_name': 'F', 'username': 'Farzam91', 'language_code': 'en'}, 'chat': {'id': 120358726, 'first_name': 'F', 'username': 'Farzam91', 'type': 'private'}, 'date': 1771890593, 'text': 'This is /com1 this is /com2', 'entities': [{'offset': 8, 'length': 5, 'type': 'bot_command'}, {'offset': 22, 'length': 5, 'type': 'bot_command'}]}}

"""
    

"""
telegram button

{'update_id': 472344185, 'callback_query': {'id': '507291191113931062', 'from': {'id': 120358726, 'is_bot': False, 'first_name': 'F', 'username': 'Farzam91', 'language_code': 'en'}, 'message': {'message_id': 358, 'from': {'id': 8176918185, 'is_bot': True, 'first_name': 'telrag', 'username': 'telrag_bot'}, 'chat': {'id': 120358726, 'first_name': 'F', 'username': 'Farzam91', 'type': 'private'}, 'date': 1772053861, 'text': 'Document 0:\nunique_id: 246 Kha intra re rec kon', 'entities': [{'offset': 0, 'length': 11, 'type': 'bold'}, {'offset': 23, 'length': 3, 'type': 'code'}], 'reply_markup': {'inline_keyboard': [[{'text': '❌ Delete', 'callback_data': '246'}]]}}, 'chat_instance': '-5702004449068403665', 'data': '246'}}

"""