<<<<<<< HEAD
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
from django.http import JsonResponse
from pgvector.django import L2Distance
from celery import shared_task

def similarity_search(conversation,input_text,num):
    """
    This function search for top num of similar text to input text
    """

    rag_toolkit = RAGToolKit()
    input_text_embedding = rag_toolkit.embedder([input_text])[0]

    # if we are in demo we have to filter similar embeddings to just use default documents and the documents which are created for the current conversation
    # each Chunk object has a document field, each Document model object may have a user_message field or not, if there is not user message it is considered a general document and its ok, if not it should check the Message object from user_message and get the conversation field, if Conversation model object was the same it's ok and can be passed.
    #.filter(chunk__document__user_message__conversation = conversation)
    similar_embeddings = Embedding.objects.order_by(L2Distance('vector', input_text_embedding))[:num]
    return input_text_embedding,similar_embeddings

def similarity_score(input_embedding : np , similar_embeddings : List[Embedding]):
    embeddings = np.array([embedding.vector for embedding in similar_embeddings])
    return np.dot(input_embedding.reshape(1,384),embeddings.T)


def ingestion_process(transaction_type , json_content,chat_id,is_new) -> Document:
    with transaction.atomic():
        telegram_object = TelegramMessage.objects.create(transaction_type=transaction_type , json_content = json_content) # True means receving (False is for sending)
        # print('telegram object has been created' , telegram_object)

        telegram_object.chat_id = chat_id
        telegram_object.save()

        document_object = process_telegram_object(telegram_object,is_new)
        # print('document object has been created', document_object)

        if document_object:
            chunk_objects = creating_chunk_objects(document_object)
            # print('Chunk(s) jas been created' , chunk_objects)

            creating_embedding_objects(chunk_objects)
            # print('Embeddings has been created' , embedding_objects)

            return document_object
        else:
            return False
    

def process_telegram_object(telegram_object:TelegramMessage,is_new=True):
    print(process_telegram_object.__name__)

    doc_object = Document.objects.create(telegram_message=telegram_object)
    data = telegram_object.data()
    parsed_data = telegram_message_parser(data)
    metadata = parsed_data['metadata']
    message_data = parsed_data['data']

    for i in metadata:
        if i == 'caption':
            doc_object.caption = metadata[i]
            doc_object.save()
        if not is_new: # it means that it is a reply message from telegram
            if i == 'reply_message_id':
                user_message = Message.objects.filter(tg_id = metadata[i]).first() # it will get the message which is related to the original message which contains user question (the question we actually are going to answer)
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

        elif data == 'voice':
            """
            sample of parsed data:

            {'metadata': {}, 'data': {'voice': {'duration': 8, 'mime_type': 'audio/ogg', 'file_id': 'AwACAgQAAxkBAAOgaZe-d0yP3eul-peB6j1HGdD3pssAAlsaAAKYusFQlwt-Nvvor0M6BA', 'file_unique_id': 'AgADWxoAApi6wVA', 'file_size': 33935}}}
            
            """
            # download using telegram
            # (note: if its not large use memory, if not use streaming.)
            # print('data: ',message_data['voice']['file_id'])
            file_data = telegram_downloader(message_data['voice']['file_id'])
            django_content_file = ContentFile(file_data)
            audio_obj = AudioContent()
            audio_obj.file.save(name=f"name.oga",content=django_content_file)
            doc_source_obj = creating_document_source(audio_obj)
            doc_object.document_source = doc_source_obj
            doc_object.save()
            return doc_object
    



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
    print(message_sender.__name__)
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

    print("Sending to 222 channel layer group")
    async_to_sync(channel_layer.group_send)(
        f"chatgroup_{conversation.pk}",
        {"type": "message_handler", "html_response": oob_html},
    )

    return message


def fetch_message_history(instance:Message):
    print(fetch_message_history.__name__)
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

def agent_message_sender(user_message:Message,context):
    print('Sending Context to AI to answer to the question')
    message_history = fetch_message_history(user_message)

    print('-- user question --' , user_message.content)
    print('-- context --' , context)

    ragtoolkit = RAGToolKit()
    new_messages = {'role':'user','content':f"{user_message.content} \n\n available information:{context}"}

    response = ragtoolkit.openai_text_generator(message_history,new_messages)

    message_sender(
        conversation=user_message.conversation,
        content=response,
        is_agent=True
    )


def fetch_conversation_documents(instance:Conversation):
    all_messages: QuerySet[Message] = instance.messages.all()

    documents = []

    for message in all_messages:
        if message.documents.all():
            documents.append(message.documents.all())


    if documents:
        documents_flatten = []
        for doc in documents:
            for i in doc:
                documents_flatten.append(i)
        return documents_flatten
    else:
        return False
    


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



def entities_handling(message_data,chat_id):
    print(entities_handling.__name__)
    for entity in message_data['entities']:
        if entity['type'] == 'bot_command':
            command = message_data['text'][entity['offset']:entity['length']]
            if settings.DEMO:
                # get chat id and sending message to user in telegram and asking for verification
                tg_chatid , created = TelegramChatID.objects.get_or_create(chat_id=chat_id)

                if command == '/verify':
                    print('Chat_id: ', chat_id)

                    # now using chat check if user is verified or no
                    is_verified = tg_chatid.is_verified

                    if is_verified:
                        send_message(chat_id,text="You are already verified!",command=True)
                    else:
                        print('This command is for verification')
                        send_message(chat_id,text="Please send the 4 digit code in the chat",command=True)
                    return True
                
                elif command == '/getdocs':
                    docs = fetch_conversation_documents(instance=tg_chatid.conversation)
                    print(docs)
                    if docs:
                        for i,doc in enumerate(docs):
                            text = f"<strong>Document {str(i)}:</strong>\nunique_id: <code>{doc.pk}</code> {fetch_content_from_document(doc)}" 
                            send_message(chat_id=chat_id,text=text , document_id=doc.pk,command=True)
                    else:
                        send_message(chat_id=chat_id,text="oOps! no document for this conversation!")
                    return True
            else:
                if command == '/verify':
                    send_message(settings.TELEGRAM_DEFAULT_CHAT_ID,text="No Verification is Required!",command=True)
                    return True
                
                elif command =="/getdocs":
                    docs = Document.objects.all()[:10]
                    if docs:
                        for i,doc in enumerate(docs):
                            text = f"<strong>Document {str(i)}:</strong>\nunique_id: <code>{doc.pk}</code> {fetch_content_from_document(doc)}" 
                            send_message(chat_id=chat_id,text=text , document_id=doc.pk,command=True)
                    else:
                        send_message(chat_id=chat_id,text="oOps! no document!")          
                    return True
def process_user_message(instance:Message):

    content = instance.content

    # Fetch message history
    message_history = fetch_message_history(instance)

    # Fetch Context
    input_text_embedding, similar_embeddings = similarity_search(conversation=instance.conversation,input_text=instance.content , num=5)

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

    result = retreival_instance.message_categorizer(user_prompt)

    print('result: ',result)


    if result in [0,1]:
        # Enough context / context not required to answer

        ragtoolkit = RAGToolKit()
        new_messages = {'role':'user','content':f"{content} \n\n{context}"}

        response = ragtoolkit.openai_text_generator(message_history,new_messages)

        message_sender(
                conversation=instance.conversation,
                content=response,
                is_agent=True
                )
        
    elif result in [2,3]:
        # Sending to telegram
        # Temporary message 1 : waiting for sending message to the user
        message_sender(
                conversation=instance.conversation,
                content="Oops! let me find somebody and ask from them!",
                is_agent=True
                )
        
        # sending message to user
        # check demo
        if settings.DEMO:
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
        else:
            telegram_message_id = send_message(text=f"{content}")
            # Updating instance (message object) with telegram id
            instance.tg_id = telegram_message_id
            instance.save()
            print(telegram_message_id) 



    elif result in [4]:
        # send and aswer which you can not respond to this matter
        message_sender(
                conversation=instance.conversation,
                content="Sorry! I can't answer to this question!",
                is_agent=True
                )



def creating_text_content_object(content:str):
    model_object = TextContent.objects.create(content = content)
    model_object.save()

    return model_object


def creating_document_source(model_object):
    print(creating_document_source.__name__)
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

    

def transcriber(document_object:Document):
    rag_toolkit = RAGToolKit()
    return rag_toolkit.audio_to_text(document_object.document_source.content_object.file.path)


def fetch_content_from_document(document_object:Document):
    if type(document_object.document_source.content_object) is TextContent:
        return document_object.document_source.content_object.content
    elif type(document_object.document_source.content_object) is AudioContent:
        # trascribing
        if not document_object.document_source.content_object.trascription:
            print('-- path ---',document_object.document_source.content_object.file.path)
            trascription = transcriber(document_object)
            print('transcription: \n\n\n', trascription)
            # storing
            document_object.document_source.content_object.trascription = trascription
            document_object.save()
            # creting chunks
        return document_object.document_source.content_object.trascription
    else:
        print('Document object class is not supported')
        return False



def creating_chunk_objects(document_object:Document) -> List[Chunk]:

    content_for_chunk = fetch_content_from_document(document_object)

    if content_for_chunk:

        rag_toolkit = RAGToolKit()
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


def regex_for_get_verification_code(data:dict , from_id):
    import re
    text = data.get("message", {}).get("text", {})
    numbers = re.findall(r"\b[1-9]\d*\b", text)
    numbers = [int(n) for n in numbers]

    for number in numbers:
        if str(number) in data.get("message", {}).get("text", {}):
            tg_chatid = TelegramChatID.objects.filter(code=number).first()
            print(f"TG chat_id: {tg_chatid}")
            if tg_chatid:
                tg_chatid.chat_id = from_id
                tg_chatid.is_verified = True
                # also it should get conversation model from somewhere
                tg_chatid.save()
                send_message(chat_id=tg_chatid.chat_id,text="✅ verification code has been detected in your message, You are verified now")
                return JsonResponse({"result": "ok"}, status=200)
            else:
                send_message(chat_id=from_id ,text="Wrong code! Please check chat window and just send the code you are seeing on the window!")
                return JsonResponse({"result": "ok"}, status=200)
            
        else:
            print('Access Denied!!!!')
            # it should be checked if user telegram account is verified or no
            return JsonResponse({"error": "Forbidden"}, status=200) # returning 200 is crucial, otherwise requests will repeadedly be send through webhook again and again!
||||||| 6d2c1b6
=======
# Standard Library Imports
import os
import logging
import numpy as np
from asgiref.sync import async_to_sync
from typing import List
from datetime import timedelta
import time
import re

# Django imports
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet,Case, When, Value, CharField,Max, Q,F,FloatField
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models.expressions import ExpressionWrapper
from django.db import IntegrityError

# Other libraries import
from dotenv import load_dotenv
from channels.layers import get_channel_layer
from pgvector.django import L2Distance

# Local imports
import chat.constants as constants
from .models import Conversation, Message,DocumentSource , TelegramMessage,Document, Chunk, Embedding, TextContent,AudioContent, RagComponent,RAGPipeline
from .utils.telegram import send_message,telegram_message_parser,telegram_downloader
from .utils.rag import LLM,latency_calculator,ModelCost,audio_to_text,embedder,NLPToolKit
from .utils.utils import Utils

# loading env variables
load_dotenv()

# Creating an instance of logging object
logger = logging.getLogger(__name__)


def hybrid_search(search_keyword:str,input_text_embedding,top_k:int,beta:float,conversation:Conversation=None)->QuerySet[Embedding]:

    """
    hybrid search using pgvector library in postgresql database, both keyword and semantic search
    - search_keyword : The query for performing a keyword (lexical) search within the database.
    - input_text_embedding : The embedded input text used by the retriever for semantic search.
    - top_k : Number of documents to be retrieved
    - beta : a value between 0 and 1 determines the ratio between 2 kind of search, beta=0, 100% result comes from semantic search, beta=1 , 100% comes from keyword search
    - conversation: the conversatin object for the chat: Demo usage
    """

    # converting user text keyword to -> PostgreSQL search query
    query = SearchQuery(search_keyword)

    result = (
        Embedding.objects

        # adding some temporary computed fields (search,rank,distance),
        .annotate(

            # Turns the text column into a searchable vector,
            search=SearchVector('chunk__text'), 

            # Computes keyword relevance score, Higher = better keyword match
            # F('search') gets the value of search! (so there is comparsinon between serach column and query value for each row)
            keyword_score=SearchRank(F('search'), query),

            # Computes semantic distance
            distance=L2Distance('vector', input_text_embedding),
            # Convert distance -> similarity
            semantic_score=ExpressionWrapper(
                1 / (1 + F("distance")),
                output_field=FloatField(),
            ),

            # Final weighted hybrid score
            hybrid_score=ExpressionWrapper(
                beta * F("keyword_score") +
                (1 - beta) * F("semantic_score"),
                output_field=FloatField(),
            ),
            category = F("chunk__document__category")
        )
        # Highest keyword match first (-rank) , Then best semantic similarity (distance ascending)
        .order_by("-hybrid_score")
    )

    if conversation:
        result = result.filter(Q(chunk__document__conversation=conversation) | Q(chunk__document__is_initial=True))[:top_k]
    else:
        result = result.filter(chunk__document__is_initial=True)[:top_k]


    return result


def similar_category(category:str):
    """
    This function query the database and will find number of all documents with the same category
    """

    result = Document.objects.filter(
        category=category
    ).values_list('category' , flat=True)

    return result

def ingestion_process(transaction_type:bool , json_content,chat_id:int,is_new:bool) -> Document:
    """
    This function handles ingestion process for the messages which come from telegram. and returns a Document object, if ingestion process be valid.

    Arguments
    - transaction_type: determines the direction of the message, Send (send from app) -> False , Receive (send from user) -> True
    - json_content: the json output from telegram webhook
    - chat_id: user chat id
    - is_new: is the message a new message or a reply to another message
    """
    with transaction.atomic():
        telegram_object = TelegramMessage.objects.create(transaction_type=transaction_type , json_content = json_content) # True means receving (False is for sending)
        # print('telegram object has been created' , telegram_object)

        telegram_object.chat_id = chat_id
        telegram_object.save()

        document_object = process_telegram_object(telegram_object,is_new)
        # print('document object has been created', document_object)

        if document_object:
            chunk_objects = creating_chunk_objects(document_object)
            # print('Chunk(s) jas been created' , chunk_objects)

            creating_embedding_objects(chunk_objects)
            # print('Embeddings has been created' , embedding_objects)

            return document_object
        else:
            return False
    
def process_telegram_object(telegram_object:TelegramMessage,is_new=True):
    """
    This method will process the telegram object, which is stored in the database and returns Document object
    
    """

    conversation = Conversation.objects.get(chat_id=telegram_object.chat_id )
    doc_object = Document.objects.create(conversation=conversation,telegram_message=telegram_object)
    data = telegram_object.data()
    parsed_data = telegram_message_parser(data)
    metadata = parsed_data['metadata']
    message_data = parsed_data['data']

    if not is_new:
        user_original_message_tg_id = metadata.get('reply_message_id',{})

    for i in metadata:
        if i == 'caption':
            doc_object.caption = metadata[i]
            doc_object.save()
        if not is_new:
            user_message = Message.objects.filter(tg_id = metadata[i]).first() # it will get the message which is related to the original message which contains user question (the question we actually are going to answer)
            if user_message:
                doc_object.user_message = user_message
                doc_object.save()
            else:
                print('This telegram message is a reply to a message, but the message is not in the database, shows that it might be replying to a telegram client message or any other message')


    for data in message_data:
        if data == 'text':
            original_message_content = ''
            if not is_new:
                user_original_message = Message.objects.filter(tg_id=user_original_message_tg_id).first()
                if user_original_message:
                    original_message_content = user_original_message.content + ': '
            model_object = creating_text_content_object(content = f"{original_message_content} {message_data[data]}")
            doc_source_obj = creating_document_source(model_object)
            doc_object.document_source = doc_source_obj
            doc_object.save()
            return doc_object

        elif data == 'voice':
            """
            sample of parsed data:

            {'metadata': {}, 'data': {'voice': {'duration': 8, 'mime_type': 'audio/ogg', 'file_id': 'dgDeAgQAAxkBAAOgaZe-d0eu5eul-rrtwj1HGdD3pssAAlsaAAKYusFQlwt-Nvvor0M6BA', 'file_unique_id': 'AgADWxoAApi6wVA', 'file_size': 33935}}}
            
            """
            duration_threshold = constants.VOICE_DURAITION_THRESHOLD
            duration = message_data.get('voice',{}).get('duration',{})
            if duration < duration_threshold:
                file_data = telegram_downloader(message_data['voice']['file_id'])
                django_content_file = ContentFile(file_data)
                audio_obj = AudioContent()
                audio_obj.file.save(name=f"voice.oga",content=django_content_file)
                doc_source_obj = creating_document_source(audio_obj)
                doc_object.document_source = doc_source_obj
                doc_object.save()
                return doc_object
            send_message(chat_id=telegram_object.chat_id,text="Demo restrictions: Please make sure your voice duration is less than 60 seconds.")
            return False
    
def message_operation( message):
    """
    returning proper html code with div tags
    """
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
    """
    For sending message in the conversation, using django channel consumer
    """
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
    """
    Fetching all messages related to 1 specific conversation, to provide context history for AI asasistant
    """
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

def agent_message_sender(user_message:Message,context):
    """
    Sending messages to conversation, by ai assistant
    
    """
    logger.info('Sending Context to AI to answer to the question')
    message_history = fetch_message_history(user_message)

    # Creating an instance of RAGPipeline
    ragpipeline = RAGPipeline.objects.create()

    # Creating an instance of dispatcher
    dispatcher = Dispatcher(ragpipeline)

    new_messages = {'role':'user','content':f"{user_message.content} \n\n available information:{context}"}

    completion_content = dispatcher.text_generation_component(message_history,new_messages)
    
    message_sender(
        conversation=user_message.conversation,
        content=completion_content,
        is_agent=True
    )

def fetch_conversation_documents(instance:Conversation):
    """
    getting all documents related to 1 specific conversation: Demo Usage
    
    """
    all_messages: QuerySet[Message] = instance.messages.all()

    documents = []

    for message in all_messages:
        if message.documents.all():
            documents.append(message.documents.all())


    if documents:
        documents_flatten = []
        for doc in documents:
            for i in doc:
                documents_flatten.append(i)
        return documents_flatten
    else:
        return False
    
def message_sender_custom(conversation:Conversation,message):
    """
    Sending customized message to user through consumer
    
    """
    channel_layer = get_channel_layer()
    html = render_to_string("telegram.html",{"chat_id_request": message})

    oob_html = ('<div id="messages" hx-swap-oob="beforeend" class="chat-container">'+ html+ "</div>")

    try:
        async_to_sync(channel_layer.group_send)(
            f"chatgroup_{conversation.pk}",
            {"type": "message_handler", "html_response": oob_html},
        )
    except ValueError as e:
        print(f"Cannot send message to group, reason: {e}")
    return True

def entities_handling(message_data,chat_id):
    """
    This function is for handling entities input from telegram messages, entities are telegram commands, this function job is detecting the command and respond as it required
    
    """
    for entity in message_data['entities']:
        if entity['type'] == 'bot_command':
            command = message_data['text'][entity['offset']:entity['length']]

            # get chat id and sending message to user in telegram and asking for verification
            conversation = Conversation.objects.get(chat_id=chat_id)
            
            if command == '/getdocs':
                docs:List[Document] = conversation.conv_documents.all()
                print(docs)
                if docs:
                    for i,doc in enumerate(docs):
                        text = f"<strong>Document {str(i)}:</strong>\nid: <code>{doc.pk}</code>\nsummary: {fetch_content_from_document(doc)}" 
                        send_message(chat_id=chat_id,text=text , document_id=doc.pk,command=True)
                else:
                    send_message(chat_id=chat_id,text="oOps! no document for this conversation!")
                return True
            
            elif command == '/refresh':
                conversation = Conversation.objects.filter(chat_id=chat_id).first()
                if conversation:
                    user = conversation.user
                    user.delete()
                    send_message(chat_id=chat_id,text="Conversation has been deleted!")

def user_message_categorizer(message:Message, ragpipeline:RAGPipeline):
    """
    This method is for categorizing user messages in the conversation, like of the message is in the knowledge scope of AI assistant or not.

    the output is providing both context and the result, context comes from hybrid search (inputing user query), so instead of re-searching this context will be return alongside the result which is an integer, which ranges from 0 to 3 and each of them leads to a different flow.
    """
    dispatcher = Dispatcher(ragpipeline)

    content = message.content  
    conversation=message.conversation

    # RAG Component
    rewrited_query = dispatcher.query_rewriter_component(content)

    # RAG Component 
    input_text_embedding = dispatcher.embedding_component(rewrited_query)

    # RAG Component 
    context = dispatcher.hybrid_search_component(conversation,content,input_text_embedding, top_k=5)

    logger.info(f"Similar Documents from Hybrid Search: {context}")

    # RAG Component
    result = dispatcher.message_categorizing_component('categorizing' ,content ,context)
    logger.info(f"result from message_categorizer: {result}")
    return context,result

def process_user_message(message:Message):
    """
    This function is for processing user message in the conversation
    """

    # Creating an instance of RAGPipeline
    ragpipeline = RAGPipeline.objects.create()

    # Creating an instance of dispatcher
    dispatcher = Dispatcher(ragpipeline)

    content = message.content
    conversation=message.conversation
    
    context,result = user_message_categorizer(message,ragpipeline)

    logger.info(f"Message Categorizer Result: {result}")
    
    # Fetch message history
    message_history = fetch_message_history(message)

    if result in [0,1]:
        logger.info("Question can be answered with available information")
        # Enough context / context not required to answer
        new_messages = {'role':'user','content':f"User question: {content}\n\nAvailable information: {context}"}

        # RAG Component
        completion_content = dispatcher.text_generation_component(message_history,new_messages)

        message_sender(
                conversation=conversation,
                content=completion_content,
                is_agent=True
                )
        
    elif result in [2]:
        logger.info("Question can not be answered with provided context")
        # Sending to telegram
        # Temporary message 1 : waiting for sending message to the user
        message_sender(
                conversation=conversation,
                content=constants.NO_INFORMATION_MESSAGE,
                is_agent=True
                )

        if conversation.chat_id:
            chat_id = conversation.chat_id
            
            firstname = message.conversation.user.first_name
            text = constants.telegram_message_support.format(firstname=firstname , content=content)

            telegram_message_id = send_message(chat_id=chat_id,text=text)

            # Updating instance (message object) with telegram id
            message.tg_id = telegram_message_id
            message.save()
            print(telegram_message_id) 
        else:
            code = message.conversation.pk
            conversation.code = code

            conversation.save()

            message_sender_custom(conversation=message.conversation,message=constants.DEMO_TELEGRAM_HUMAN_ROLE_MESSAGE)

            code_message = constants.demo_telegram_verify_messsage.format(code=code)
            message_sender_custom(conversation=message.conversation,message=code_message)


    elif result in [3]:
        logger.info("Question is out of scope of answering")
        # send and aswer which you can not respond to this matter
        message_sender(
                conversation=message.conversation,
                content=constants.CANT_ANSWER_MESSAGE,
                is_agent=True
                )


def creating_text_content_object(content:str):
    """
    This method is for creating text context object, for using as a document source
    """
    try:
        model_object = TextContent.objects.create(content = content)
        return model_object
    except IntegrityError as e:
        raise IntegrityError(f"IntegrityError: Unique content violation, content object should be unique, you probably are inserting similar documents into the database, Error description:\n\n\n{e}")
    
    
    

def creating_document_source(model_object):
    """
    This method is for creating document source object
    """
    content_type_obj = ContentType.objects.get_for_model(model_object.__class__)

    doc_source_obj = DocumentSource.objects.create(
        content_type = content_type_obj, # content type object, which is linked to the actual object
        object_id = model_object.pk # the specfific id of the that actual object (not content type object)
    )

    return doc_source_obj

def creating_document_object(document_source, category="user_input", conversation=None, is_initial=False, caption=None,user_message=None,telegram_message=None) -> Document:

    """
    This method is for creating document object
    
    """

    doc_object = Document.objects.create(document_source = document_source)

    if conversation:
        doc_object.conversation = conversation

    if category:
        doc_object.category = category

    if is_initial:
        doc_object.is_initial = is_initial

    if caption:
        doc_object.caption = caption
    
    if user_message:
        doc_object.user_message = user_message

    if telegram_message:
        doc_object.telegram_message = telegram_message

    doc_object.save()

    return doc_object

def transcriber(document_object:Document):
    """
    This method is for converting voices to trasciption from user telegram messages which are not pure text and are voices.
    """
    return audio_to_text(document_object.document_source.content_object.file.path)

def fetch_content_from_document(document_object:Document):
    """
    This function is for getting content from document object, as document object uses content type object, it should detect which type of content is and then going for getting each content in it's own way
    """

    if type(document_object.document_source.content_object) is TextContent:
        return document_object.document_source.content_object.content
    elif type(document_object.document_source.content_object) is AudioContent:
        if not document_object.document_source.content_object.trascription:
            logger.info(f"file path: {document_object.document_source.content_object.file.path}")
            trascription = transcriber(document_object)
            logger.info(f"Transcription: {trascription}")

            # saving in the database
            document_object.document_source.content_object.trascription = trascription
            document_object.save()
            # creting chunks
        return document_object.document_source.content_object.trascription
    else:
        logger.info('Document object class is not supported')
        return False

def creating_chunk_objects(document_object:Document) -> List[Chunk]:
    """
    This method is for creating chunk object from Document
    """
    content_for_chunk = fetch_content_from_document(document_object)
    
    if content_for_chunk:

        nlp_toolkit = NLPToolKit()
        chunks = nlp_toolkit.split_text(text=content_for_chunk)

        objects = Chunk.objects.bulk_create(
            [
                Chunk(chunk_id = i , text = chunk , document = document_object) for i, chunk in enumerate(chunks)
            ] 
        )
        return objects

def creating_embedding_objects(chunks):
    """
    Creating Embedding objects from chunk objects
    """

    chunks_text = [chunk.text for chunk in chunks]
    embeddings = embedder(model=constants.HF_EMBEDDING_MODEL,text=chunks_text)

    objects = Embedding.objects.bulk_create(
        [
            Embedding(chunk=chunk, vector=embedding)
            for chunk, embedding in zip(chunks, embeddings)
        ]
    )

    return objects

def regex_for_get_verification_code(data:dict , from_id):
    """
    This function is for detecting numbers in the telegram messages from user
    """
    
    text = data.get("message", {}).get("text", {})
    numbers = re.findall(r"\b[1-9]\d*\b", text)
    numbers = [int(n) for n in numbers]

    for number in numbers:
        if str(number) in data.get("message", {}).get("text", {}):
            conversation = Conversation.objects.filter(code=number).first()
            print(f"Conversation: {conversation}")
            if conversation:
                conversation.chat_id = from_id
                conversation.is_verified = True
                # also it should get conversation model from somewhere
                conversation.save()
                send_message(chat_id=conversation.chat_id,text="✅ A verification code was detected in your message. You are now verified.")
                send_message(chat_id=conversation.chat_id,text="""Quick guide:\n
1. Send a direct message on Telegram → it will be stored as context.\n
2. Reply to a message from the agent → it will be stored as context and immediately sent to the agent to answer the question.\n
3. Get all contexts (each context as a unique document): /getdocs """)
                message_sender_custom(conversation=conversation, message=f"<br>✅ Your telegram account is linked to this conversation!")

                # Now we try to fetch the last message which is sent from user to the support telegram to have it answered right after verification
                last_message:Message = conversation.messages.filter(is_agent=False).last()
                if last_message:
                    telegram_message_id = send_message(chat_id=conversation.chat_id,text=f"""💬 A customer named <b>{conversation.user.first_name}</b> asked the following question:\n\n<b>{last_message.content}</b>\n\n🔻 I don't have enough information to answer it. Please reply to this message with your response so I can answer it correctly.""")
                    # note: as user gonna reply to this messsage, we have to store it as a telegram message id
                    last_message.tg_id = telegram_message_id
                    last_message.save()
                return JsonResponse({"result": "ok"}, status=200)
            else:
                send_message(chat_id=from_id ,text="Invalid number. Please check the chat window and enter the code shown there.")
                return JsonResponse({"result": "ok"}, status=200)
            
        else:
            print('Access Denied!!!!')
            # it should be checked if user telegram account is verified or no
            return JsonResponse({"error": "Forbidden"}, status=200) # returning 200 is crucial, otherwise requests will repeadedly be send through webhook again and again!
        


def delete_unused_conversation():
    """
    Deleting unused conversation by User
    """
    #getting conversations
    threshold = timezone.now() - timedelta(minutes=30)
    conversations = Conversation.objects.annotate(
        last_msg_time=Max("messages__created_at")
    ).filter(
        Q(last_msg_time__lt=threshold) |
        Q(last_msg_time__isnull=True, created_at__lt=threshold)
    )
    
    for conversation in conversations:
        message_sender_custom(conversation , """This conversation has expired due to inactivity. Please go to the <a href="https://tel‍rag.site">homepage</a and start a new one.""")
        conversation.delete()



def load_initial_documents(abs_data_dir):
    """

    this function returns a dictionary which have category name as a key and file path as value, for example:

    {'crm_refund' : 'chat/management/commands/initial_data/telmart/crm/refund.txt',
    'general_general' : 'chat/management/commands/initial_data/telmart/general/general.txt',
    ...,}

    This method is used for intial_data_db_insert function

    """

    txt_files_dict = {}
    dirs = os.listdir(abs_data_dir)
    for dir in dirs:
        txt_file_path = os.path.join(abs_data_dir,dir)
        txt_files = os.listdir(txt_file_path)
        txt_files_full_path_list = []
        for txt_file in txt_files:
            txt_file_full_path = os.path.join(txt_file_path,txt_file)
            txt_files_full_path_list.append(txt_file_full_path)
        txt_files_dict[f"{dir}"] = txt_files_full_path_list
    return txt_files_dict


def intial_data_db_insert(data_dir)->QuerySet[Embedding]:
    abs_data_dir = os.path.join(settings.BASE_DIR,data_dir)
    txt_files_dict = load_initial_documents(abs_data_dir)
    number_of_documents = 0

    try:
        for category in txt_files_dict:
            for file_path in txt_files_dict[category]:
                print(f"category : {category} - filepath: {file_path}")
                with transaction.atomic():
                    with open(file_path,'r') as text_file:
                        text_string = text_file.read()
                    text_content_object = creating_text_content_object(content=text_string)
                    if text_content_object:
                        doc_source_object = creating_document_source(model_object=text_content_object)
                        if doc_source_object:
                            doc_object = creating_document_object(document_source=doc_source_object,category=category , is_initial=True)
                            if doc_object:
                                chunk_objects = creating_chunk_objects(document_object=doc_object)
                                if chunk_objects:
                                    embedding_objects = creating_embedding_objects(chunks=chunk_objects)
                                    if embedding_objects:
                                        print(f"Embedding has been created for: {category}")
                                        number_of_documents+=1
                    else:
                        return False
                    
        print(number_of_documents)
        return number_of_documents
    except Exception as e:
        logger.error(e)

def rag_component_creator(
        ragpipeline:RAGPipeline,
        component_name:str,
        latency:float,
        conversation:Conversation=None,
        input_text:str=None,
        output_text:str=None,
        model:str=None,
        currency:str=None,
        embedding_cost:float=None,
        input_cost:float=None,
        output_cost:float=None
):
    """
    
    This method is for creating rag component
    """
    ragcomponent = RagComponent.objects.create(
        ragpipeline = ragpipeline,
        component_name = component_name,
        conversation = conversation,
        input_text = input_text,
        output_text = output_text,
        model = model,
        currency = currency,
        embedding_cost = embedding_cost,
        input_cost = input_cost,
        output_cost = output_cost,
        latency = latency
    )

    if ragcomponent:
        return True
    

class Dispatcher():
    """
    getting the job name and distributing to the right function and then returning the output for adding to the database

    jobs:
        - message_categorizer
        - embedder
        - text_generator
        - 
    """
    def __init__(self,rag_pipeline:RAGPipeline):
        self.rag_pipeline = rag_pipeline
        self.data = {
            'completion' : None,
            'response' : None,
            'embedding' : None,
        }
        super().__init__()


    def save_to_db(self,rag_component,start_time,data):
        """
        data : {
            'chat_completion' : chat_completion,
            'response' : response,
            'embedding' : embedding,
        }
        """
        costmodel = ModelCost(rag_component)
        cost = costmodel.cost_model_dispatcher(data)
        latency = latency_calculator(start_time)

        

        # Merging 2 dictionary
        rag_component_dict = {'ragpipeline':self.rag_pipeline,'component_name' : rag_component , 'latency' : latency} | cost

        logger.info(f"Rag Component Details: {rag_component_dict}")

        # Saving to db
        rag_component_creator(**rag_component_dict)

    def embedding_component(self,content):
        # Set start time
        start_time = time.time()
        model = constants.HF_EMBEDDING_MODEL

        utils = Utils()
        rag_component = constants.RAG_COMPONENTS["Embedder"]
        input_text_embedding = embedder(model,text=[content])[0]

        self.save_to_db(rag_component,start_time,self.data)

        return input_text_embedding
    
    def hybrid_search_component(self,conversation:Conversation|None,content:str,input_text_embedding,top_k):

        similar_embeddings = hybrid_search(conversation=conversation,search_keyword=content,input_text_embedding=input_text_embedding ,beta=constants.BETA, top_k=top_k)
        data = {}

        context =''
        if similar_embeddings:
            similar_text = "\n\n--------------------\n\n".join([embedding_obj.chunk.text for embedding_obj in similar_embeddings])
            context = similar_text

        return context

    def message_categorizing_component(self,job,content,context):
        # Set start time
        start_time = time.time()
        model = constants.OPENAI_CHAT_MODEL
        llm = LLM(model)

        user_prompt = f"""
            User Question: {content}\n\n
            Available Information: {context}
        """
        rag_component = constants.RAG_COMPONENTS["Message Categorizer"]
        completion = llm.openai_classifier(user_prompt,job)
        self.data['completion'] = completion
        self.save_to_db(rag_component,start_time,self.data)

        content = completion.choices[0].message.content
        # Check if validator fails what to return
        validator = llm.get_validator(job)
        result = validator(content).result

        return result

        # Saving information into database
    def text_generation_component(self,message_history,new_messages):
        start_time = time.time()
        model = constants.OPENAI_CHAT_MODEL
        rag_component= constants.RAG_COMPONENTS["Text Generator"]
        llm = LLM(model=model)
        completion = llm.openai_text_generator(message_history,new_messages)
        self.data['completion'] = completion
        self.save_to_db(rag_component , start_time , self.data)

        return completion.choices[0].message.content
    
    def query_rewriter_component(self,original_text):
        start_time = time.time()
        model = constants.OPENAI_CHAT_MODEL
        rag_component= constants.RAG_COMPONENTS["Query Rewriting"]
        llm = LLM(model=model)
        response = llm.openai_text_rewriter(original_text)
        result = response.output_text
        self.data['response'] = response
        self.save_to_db(rag_component , start_time , self.data)

        return result
        
>>>>>>> demo
