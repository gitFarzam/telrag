from django.contrib.contenttypes.models import ContentType
from .models import Conversation, Message,DocumentSource , TelegramMessage,Document, Chunk, Embedding, TextContent,AudioContent, TelegramChatID
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
from django.db.models import QuerySet,Case, When, Value, CharField
from django.conf import settings
import json
import numpy as np
import time

def similarity_search(input_text,num):
    """
    This function search for top num of similar text to input text
    
    """
    from pgvector.django import L2Distance

    rag_toolkit = RAGToolKit()
    input_text_embedding = rag_toolkit.embedder([input_text])[0]

    similar_embeddings = Embedding.objects.order_by(L2Distance('vector', input_text_embedding))[:num]
    # results = (
    #     Embedding.objects
    #     .annotate(distance=L2Distance("vector", text_embedding))
    #     .order_by("-distance") 
    # )

    # print('distance: ' , results[0].distance , 'similarty: ',1 / (1 + results[0].distance))

    # print('similars: ',similar_embeddings)
    return input_text_embedding,similar_embeddings





def similarity_score(input_embedding : np , similar_embeddings : List[Embedding]):

    embeddings = np.array([embedding.vector for embedding in similar_embeddings])

    return np.dot(input_embedding.reshape(1,384),embeddings.T)



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
                print('Sending Context to AI to answer to the question')
                message_history = fetch_message_history(document_object.user_message)

                print('-- user question --' , document_object.user_message.content)
                context = "\n ".join([chunk.text for chunk in chunk_objects])
                print('-- context --' , context)

                ragtoolkit = RAGToolKit()
                new_messages = {'role':'user','content':f"{document_object.user_message.content} \n\n available information:{context}"}

                response = ragtoolkit.openai_text_generator(message_history,new_messages)

                message_sender(
                    conversation=document_object.user_message.conversation,
                    content=response,
                    is_agent=True
                )

            return True


def message_group_creator(message:Message):
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
    message = Message.objects.create(
            conversation=conversation,
            content=content
        )

    if is_agent:
        message.is_agent = True
        message.save()
        # Here content should be sent to another bot to get a response, through signals

    oob_html = message_operation(message)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chatgroup_{conversation.pk}",
        {"type": "message_handler", "html_response": oob_html},
    )

    return message




def fetch_message_history(instance:Message):
    return list(
        (
        instance.conversation.messages
        .annotate(
            role=Case(
                When(is_agent=True, then=Value("assistant")),
                default=Value("user"),
                output_field=CharField(),
            )
        )
        .values("role", "content")
    )
    )


def ask_user_telegram_chatid(conversation:Conversation,code):
    message = f"""
    Please send verify your telegram account to be able to work as an context provider.\n<br><br>
    1. open your telegram application\n<br>
    2. search for this chatbot in search feild: <b>@telrag_bot</b>\n<br>
    3. tap/click <b>verify</b>\n<br>
    4. send this code to the bot: {code}\n<br>
    5. wait for the bot to verify your account\n\n<br><br>

    -> After verification this window will be disapeared.
    """

    channel_layer = get_channel_layer()


    html = render_to_string(
        "message.html",
        {"chat_id_request": message}
    )

    oob_html = (
        '<div id="messages" hx-swap-oob="beforeend" class="chat-container">'
        + html
        + "</div>"
    )


    async_to_sync(channel_layer.group_send)(
        f"chatgroup_{conversation.pk}",
        {"type": "message_handler", "html_response": oob_html},
    )

    return True


def process_user_message(instance:Message):

    content = instance.content

    # Fetch message history
    message_history = fetch_message_history(instance)

    # Fetch Context
    input_text_embedding, similar_embeddings = similarity_search(input_text=instance.content , num=5)

    context =''
    if similar_embeddings:
        similar_text = "\n".join([embedding_obj.chunk.text for embedding_obj in similar_embeddings])

        # Fetch similarity scores
        score = similarity_score(input_text_embedding, similar_embeddings)
        print(score)
        context = f" \n\n available information: {similar_text}"
        


    # Check if the question is related
    retreival_instance = RetirievalNavigator(model="meta-llama/Llama-3.1-8B-Instruct",token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5")

    user_prompt = f"""
        user question/reqeust : {content}{context}

    """

    result = retreival_instance.enough_context_to_answer_detector(user_prompt)


    if result in [5]:
        # Enough context / context not required to answer

        ragtoolkit = RAGToolKit()
        new_messages = {'role':'user','content':f"{content} \n\n available information:{similar_text}"}

        response = ragtoolkit.openai_text_generator(message_history,new_messages)

        message_sender(
                conversation=instance.conversation,
                content=response,
                is_agent=True
                )
        
    elif result in [0,1,2,3]:
        # Sending to telegram

        # Temporary message 1 : waiting for sending message to the user
        message_sender(
                conversation=instance.conversation,
                content="Oops! let me find somebody and ask from them!",
                is_agent=True
                )
        

        # sending message to user


        # get chat id
        obj,created = TelegramChatID.objects.get_or_create(conversation = instance.conversation)
        if created:
            print('lets go for finding chat id')
            code = obj.pk # use pk as code for authentication!
            obj.code = code
            obj.save()
            ask_user_telegram_chatid(conversation=instance.conversation,code=code)
        else:
            if obj.chat_id:
                chat_id = obj.chat_id
                print('chat id: ',chat_id)
                telegram_message_id = send_message(chat_id=chat_id,text=f"{content}")

                # Updating instance (message object) with telegram id
                instance.tg_id = telegram_message_id
                instance.save()
                print(telegram_message_id) 
            else:
                print('Object is existed but it doesnt have a chat id value')
                ask_user_telegram_chatid(conversation=instance.conversation,code=obj.code)

        
        



    # elif result == 3:
    #     # send and aswer which you can not respond to this matter
    #     message_sender(
    #             conversation=instance.conversation,
    #             content="Sorry! I can't answer to this question!",
    #             is_agent=True
    #             )



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


    chat_id = metadata['chat_id']
    print('Chat_id: ', chat_id)
    tg_chatid = TelegramChatID(chat_id=chat_id)
    



    for i in metadata:
        if i == 'caption':
            doc_object.caption = metadata[i]
            doc_object.save()
        if i == 'message_id':
            user_message = Message.objects.filter(tg_id = metadata[i]).first()
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


        elif data == 'voice':
            """
            sample of parsed data:

            {'metadata': {}, 'data': {'voice': {'duration': 8, 'mime_type': 'audio/ogg', 'file_id': 'AwACAgQAAxkBAAOgaZe-d0yP3eul-peB6j1HGdD3pssAAlsaAAKYusFQlwt-Nvvor0M6BA', 'file_unique_id': 'AgADWxoAApi6wVA', 'file_size': 33935}}}
            
            """
            # download using telegram
            # (note: if its not large use memory, if not use streaming.)
            print('data: ',message_data['voice']['file_id'])
            file_data = telegram_downloader(message_data['voice']['file_id'])
            django_content_file = ContentFile(file_data)
            audio_obj = AudioContent()
            audio_obj.file.save(name=f"name.oga",content=django_content_file)
            doc_source_obj = creating_document_source(audio_obj)
            doc_object.document_source = doc_source_obj
            doc_object.save()

    if message_data['entities']:
        for entity in message_data['entities']:
            if entity['type'] == 'bot_command':
                command = message_data['text'][entity['offset']:entity['length']]
                if command == '/verify':
                    # get chat id and sending message to user in telegram and asking for verification
                    chat_id = metadata['chat_id']
                    print('Chat_id: ', chat_id)

                    # now using chat check if user is verified or no
                    tg_chatid = TelegramChatID(chat_id=chat_id)
                    is_verified = tg_chatid.is_verified

                    if is_verified:
                        send_message(chat_id,text="You are already verified!")
                    else:
                        print('This command is for verification')
                        send_message(chat_id,text="Please send the 4 digit code in the chat")


    return doc_object




def creating_chunk_objects(document_object:Document) -> List[Chunk]:
    rag_toolkit = RAGToolKit()

    if type(document_object.document_source.content_object) is TextContent:
        content_for_chunk = document_object.document_source.content_object.content
    elif type(document_object.document_source.content_object) is AudioContent:
        # trascribing
        print('-- path ---',document_object.document_source.content_object.file.path)
        trascription = rag_toolkit.audio_to_text(document_object.document_source.content_object.file.path)
        print('transcription: \n\n\n', trascription)
        # storing
        document_object.document_source.content_object.trascription = trascription
        document_object.save()
        # creting chunks
        content_for_chunk = document_object.document_source.content_object.trascription
        pass

    else:
        print('Content type is not compatible, just TexContent object is supported')

    chunks = rag_toolkit.split_text(text=content_for_chunk)

    objects = Chunk.objects.bulk_create(
        [
            Chunk(chunk_id = i , text = chunk , document = document_object) for i, chunk in enumerate(chunks)
        ] 
    )
    return objects

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



