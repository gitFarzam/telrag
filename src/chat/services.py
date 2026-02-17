from django.contrib.contenttypes.models import ContentType
from .models import Conversation, UserMessage, AgenMessage,DocumentSource , TelegramMessage,Document, Chunk, Embedding, TextContent
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template.loader import render_to_string
from .utils.telegram import send_message,telegram_message_parser,telegram_downloader
from .utils.agents import agent_detecting_context
from .utils.rag import RAGToolKit,RetirievalNavigator
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.db import transaction
from typing import List
import json

def similarity_search(input_text,num):
    """
    This function search for top num of similar text to input text
    
    """
    from pgvector.django import L2Distance

    rag_toolkit = RAGToolKit()
    text_embedding = rag_toolkit.embedder([input_text])[0]
    print(text_embedding)

    similar_embeddings = Embedding.objects.order_by(L2Distance('vector', text_embedding))[:num]
    # results = (
    #     Embedding.objects
    #     .annotate(distance=L2Distance("vector", text_embedding))
    #     .order_by("-distance") 
    # )

    # print('distance: ' , results[0].distance , 'similarty: ',1 / (1 + results[0].distance))

    # print('similars: ',similar_embeddings)
    return similar_embeddings


def ingestion_process(transaction_type , json_content):
    
    """
    1. processing telegram message from webhook and save the result in the database
    2. processing telegram object and save cleaned document in the database
    3. processing document object and create chunks and saving chunks in the database
    4. processing chunk objects, creating embedding and saving embedding from them
    5. sending context to live agent if it's neccessary
    
    """
    with transaction.atomic():
        telegram_object = TelegramMessage.objects.create(transaction_type=transaction_type , json_content = json_content) # True means receving (False is for sending)
        # print('telegram object has been created' , telegram_object)

        document_object = process_telegram_object(telegram_object)
        # print('document object has been created', document_object)

        chunk_objects = creating_chunk_objects(document_object)
        # print('Chunk(s) jas been created' , chunk_objects)

        embedding_objects = creating_embedding_objects(chunk_objects)
        # print('Embeddings has been created' , embedding_objects)

        if embedding_objects:
            if document_object.user_message:
                print('Sending Context to the user')
                message_sender(
                    conversation=document_object.user_message.conversation,
                    content=document_object.text,
                    is_agent=True
                )

            return True


def message_group_creator(message:UserMessage):
    """
    This function will have some logic to see how to group the messages.

    1. wait for 2 seconds before answering to the customer, they may need to send another message
    2. short messages which are not conisdered
    """



def message_operation( message):
    html = render_to_string(
        "message.html",
        {"message": message}
    )

    oob_html = (
        '<div id="messages" hx-swap-oob="beforeend" class="chat-container">'
        + html
        + "</div>"
    )

    return oob_html


def message_sender(conversation:Conversation,content,is_agent):
    if is_agent:
        message =AgenMessage.objects.create(
            conversation=conversation,
            content=content
        )
    else:
        message =UserMessage.objects.create(
            conversation=conversation,
            content=content
        )

        # Here content should be sent to another bot to get a response, through signals

    oob_html = message_operation(message)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chatgroup_{conversation.pk}",
        {"type": "message_handler", "html_response": oob_html},
    )

    return message




question_list = [
    ['I have a question about my order.','Sure, please provide your order number.'],
    ['I need to cancel my order','Sure, please provide your order number.'],
    ['Is there any discount available?','Yes, we offer a %10 discount for first-time customers.'],
    ['What is the status of my shipment?','Your shipment is currently in transit and will be delivered within 2-3 business days.'],
    ['Can I change my delivery address?','Yes, you can change your delivery address before the shipment is dispatched. Please contact our support team.'],
    ['How do I return a product?','You can return a product within 30 days of purchase by contacting our support team with your order number.'],
    ['What payment methods do you accept?','We accept all major credit cards, PayPal, and bank transfers.'],
]

def process_user_message(instance:UserMessage):






    content = instance.content

    # Check if the question is related
    retreival_instance = RetirievalNavigator(model="meta-llama/Llama-3.1-8B-Instruct",token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5")

    context_code = retreival_instance.enough_context_to_answer_detector(content)

    print(context_code)


    # if enough_context:

    #     print(f"New message: {instance.content}")

    #     # this process should be executed through a worker, so user can continue sending messages
    #     print("AI Can asnwer!!!!!")

    #     # Short answer for waiting
    #     message_sender(
    #                 conversation=instance.conversation,
    #                 content=instance.content,
    #                 is_agent=True
    #                 )
        # telegram process

        # # sending message to user
        # telegram_message_id = send_message(text=f"{content}")

        # # Updating instance (message object) with telegram id
        # instance.tg_id = telegram_message_id
        # instance.save()
        # print(telegram_message_id) 

        # receving message from webhook
        # a function for precessing telegram webhook message, parse the json and check conversation id and etc..

    # else:
        
    #     print('More context is required')

        # similar_embeddings = similarity_search(input_text=instance.content , num=5)
        # similar_text = "\n".join([
        #     embedding_obj.chunk.text for embedding_obj in similar_embeddings
        # ])

        # ragtoolkit = RAGToolKit()
        # messages_history = {'role':'user','content':'hi how are you'}
        # new_messages = {'role':'user','content':f"having this information:{similar_text}, answer this:\n {content}"}

        # result = ragtoolkit.text_generator(messages_history,new_messages)


        # print('Sorry, but your request is out of scope of this chat')
        # message_sender(
        #     conversation=instance.conversation,
        #     content="'Sorry, but your request is out of scope of this chat'",
        #     is_agent=True
        #     )

def creating_text_content_object(content:str):
    model_object = TextContent.objects.create(content = content)
    model_object.save()

    return model_object


def creating_document_source(model_object):
    content_type_obj = ContentType.objects.get_for_model(model_object.__class__)

    doc_source_obj = DocumentSource.objects.create(
        content_type = content_type_obj, # content type object, which is linked to the actual object
        object_id = model_object.pk # the specfific id of the that actual object (not content type object)
    )

    return doc_source_obj


def creating_document_object(document_source, caption=None,user_message=None,telegram_message=None) -> Document:
    doc_object = Document.objects.create(document_source = document_source)

    if caption:
        doc_object.caption = caption
    
    if user_message:
        doc_object.user_message = user_message

    if telegram_message:
        doc_object.telegram_message = telegram_message

    doc_object.save()

    return doc_object

    


def process_telegram_object(telegram_object:TelegramMessage):

    # check if it has `reply_to_message` use it for responsing to a specific question
    # check if the message is for data storage or it's just a context for this specific conversation (this part probably requires an agent for detecting this, it's not that much hard)
    # if it does not have it's for general rag

    doc_object = Document.objects.create(telegram_message=telegram_object)
    
    data = telegram_object.data()
    parsed_data = telegram_message_parser(data)
    print('Parsed data: ',parsed_data)

    metadata = parsed_data['metadata']
    message_data = parsed_data['data']

    for i in metadata:
        if i == 'caption':
            doc_object.caption = metadata[i]
            doc_object.save()
        if i == 'message_id':
            user_message = UserMessage.objects.filter(tg_id = metadata[i]).first()
            if user_message:
                doc_object.user_message = user_message
                doc_object.save()
            else:
                print('This telegram message is a reply to a message, but the message is not in the database, shows that it might be replying to a telegram client message or any other message')

    for data in message_data:
        if  data == 'text':
            model_object = creating_text_content_object(content = message_data[data])
            doc_source_obj = creating_document_source(model_object)
            doc_object.document_source = doc_source_obj
            doc_object.save()

    return doc_object
        
    if  data == 'voice':
        # download using telegram
        # if its not large use memory, if not use streaming.
        file_data = telegram_downloader()
        django_content_file = ContentFile(file_data)
        document = Document.objects.create()
        document.file.save(name=f"name",content=django_content_file)


def creating_chunk_objects(document_object:Document) -> List[Chunk]:
    rag_toolkit = RAGToolKit()

    if type(document_object.document_source.content_object) is TextContent:

        chunks = rag_toolkit.split_text(text=document_object.document_source.content_object.content)

        objects = Chunk.objects.bulk_create(
            [
                Chunk(chunk_id = i , text = chunk , document = document_object) for i, chunk in enumerate(chunks)
            ] 
        )
        return objects
    else:
        print('Content type is not compatible, just TexContent object is supported')




def creating_embedding_objects(chunks):
    rag_toolkit = RAGToolKit()

    chunks_text = [chunk.text for chunk in chunks]
    embeddings = rag_toolkit.embedder(chunks=chunks_text)

    objects = Embedding.objects.bulk_create(
        [
            Embedding(chunk=chunk, vector=embedding)
            for chunk, embedding in zip(chunks, embeddings)
        ]
    )

    return objects


def message_history(conversation:Conversation):
    Conversation


