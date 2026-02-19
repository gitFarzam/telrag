# telegram_app/telegram.py
import requests
from dotenv import load_dotenv
import os
import json
load_dotenv()

# https://api.telegram.org/bot8536509873:BAFG4ILMA39Iuhj8SQhy6hks5RspmDRs_6D/getUpdates

# https://api.telegram.org/bot8536509873:BAFG4ILMA39Iuhj8SQhy6hks5RspmDRs_6D/deleteWebhook
telegram_api_key = os.getenv('telegram_api')


def send_message(chat_id=None, text=None):
    chat_id = 120358726
    url = f"https://api.telegram.org/bot{telegram_api_key}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "message_id" : 5 
    }
    response = requests.post(url, json=payload)
    telegram_message_id = response.json()['result']['message_id']
    """
        {'ok': True, 'result': {'message_id': 34, 'from': {'id': 8176918185, 'is_bot': True, 'first_name': 'telrag', 'username': 'telrag_bot'}, 'chat': {'id': 120358726, 'first_name': 'F', 'username': 'Farzam91', 'type': 'private'}, 'date': 1770237370, 'text': 'Hey! Somebody have a question:\nU'}}
    """

    return telegram_message_id





def telegram_message_parser(json_data_dict:dict):

    message = json_data_dict.get('message',None)
    # print('message data: ',message)
    message_keys = message.keys()

    parsed_data = {'metadata':{} , 'data':{}}

    # Define default variables
    user_message_id = None

    if 'caption' in message_keys :
        parsed_data['metadata']['caption'] = message.get('caption')

    if 'reply_to_message' in message_keys :
        parsed_data['metadata']['message_id'] = message['reply_to_message']['message_id']

    if 'text' in message_keys :
        parsed_data['data']['text'] = message.get('text')

    if 'photo' in message_keys :
        parsed_data['data']['photo'] = message.get('photo')

    if 'voice' in message_keys :
        parsed_data['data']['voice'] = message.get('voice')

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

    return file_data
    # with open("sample.oga", "wb") as f:
    #     f.write(file_data)

if __name__ == "__main__":
    telegram_downloader()


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
    