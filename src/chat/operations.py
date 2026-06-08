from .tasks import task_new_message,task_reply_message,task_entities_handling,task_button_handling
from .utils.telegram import telegram_message_parser
import logging

# Creating an instance of the logging object
logger = logging.getLogger(__name__)


def telegram_message_processor(transaction_type:bool , json_content:dict):
    
    parsed_data = telegram_message_parser(json_content)
    message_type = parsed_data['type']
    metadata = parsed_data['metadata']
    message_data = parsed_data['data']
    message_id = parsed_data['metadata']['message_id']
    chat_id = metadata['chat_id']

    logger.info(f"Parsed Data: {parsed_data}")
    
    if message_type == 'new':
        task_new_message.delay(transaction_type,json_content,chat_id,message_id)

    elif message_type == 'reply':
        task_reply_message.delay(transaction_type,json_content,chat_id,message_id)

    elif message_type == 'entities':
        task_entities_handling.delay(message_data,chat_id)

    elif message_type == 'button':
        # Deleting documents button
        task_button_handling.delay(message_data,chat_id)



