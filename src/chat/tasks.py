from celery import shared_task
from .services import ingestion_process,fetch_content_from_document,agent_message_sender,entities_handling,delete_unused_conversation
from .utils.telegram import send_message
from .models import Document
from asgiref.sync import async_to_sync
from .models import Conversation

@shared_task
def task_new_message(transaction_type,json_content,chat_id,message_id):
    document_object = ingestion_process(transaction_type,json_content,chat_id,is_new=True)
    if document_object:
        send_message(text=f"Document has been created, ID: {document_object.pk}",reply_to_message_id=message_id)
    else:
        send_message(text=f"Creating Document was unsuccessfull",reply_to_message_id=message_id)

@shared_task
def task_reply_message(transaction_type,json_content,chat_id,message_id):
    document_object = ingestion_process(transaction_type,json_content,chat_id,is_new=False)
    if document_object:
        send_message(text=f"Document has been created, ID: {document_object.pk}",reply_to_message_id=message_id)
        agent_message_sender(document_object.user_message,context=fetch_content_from_document(document_object))
    else:
        send_message(text=f"Creating Document was unsuccessfull",reply_to_message_id=message_id)

@shared_task
def task_entities_handling(message_data,chat_id):
    # getting document in normal mode, is for all docs, in demo mode is just for a specific hat
    result = entities_handling(message_data,chat_id)
    if result:
        print('Document has been sent to you in telegram!')


@shared_task
def task_button_handling(message_data,chat_id):
    del_document_id = message_data.get('del_document_id')
    obj = Document.objects.filter(pk=del_document_id).first()
    
    if obj:
        obj_pk = obj.pk
        obj.delete()
        send_message(chat_id=chat_id,text=f"Document {obj_pk} has been deleted: ",command=True)
    else:
        send_message(chat_id=chat_id,text=f"Document does not exist!",command=True)


@shared_task
def task_delete_unused_conversation():
    result = delete_unused_conversation()
    print(result)