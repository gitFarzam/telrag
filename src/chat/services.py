# Standard Library Imports
import os
import logging
import numpy as np
from asgiref.sync import async_to_sync
from typing import List
from datetime import timedelta

# Django imports
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet,Case, When, Value, CharField,Max, Q,F
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

# Other libraries import
from dotenv import load_dotenv
from channels.layers import get_channel_layer
from pgvector.django import L2Distance

# Local imports
import chat.constants as constants
import chat.prompts as prompts
from .models import Conversation, Message,DocumentSource , TelegramMessage,Document, Chunk, Embedding, TextContent,AudioContent
from .utils.telegram import send_message,telegram_message_parser,telegram_downloader
from .utils.rag import NLPToolKit,RetrievalToolKit

# loading env variables
load_dotenv()

# Creating an instance of logging object
logger = logging.getLogger(__name__)

def similarity_search(conversation,input_text,num):
    """
    This function search for top num of similar text to input text
    """

    rag_toolkit = NLPToolKit()
    input_text_embedding = rag_toolkit.embedder([input_text])[0]

    # if we are in demo we have to filter similar embeddings to just use default documents and the documents which are created for the current conversation
    # each Chunk object has a document field, each Document model object may have a user_message field or not, if there is not user message it is considered a general document and its ok, if not it should check the Message object from user_message and get the conversation field, if Conversation model object was the same it's ok and can be passed.
    #.filter(chunk__document__user_message__conversation = conversation)
    similar_embeddings = Embedding.objects.filter(chunk__document__conversation=conversation).order_by(L2Distance('vector', input_text_embedding))[:num]
    return input_text_embedding,similar_embeddings

def hybrid_search(conversation,user_query,input_text,num):

    rag_toolkit = NLPToolKit()
    input_text_embedding = rag_toolkit.embedder([input_text])[0]


    # converting user text keyword to -> PostgreSQL search query
    query = SearchQuery(user_query)

    return (
        Embedding.objects

        # adding some temporary computed fields (search,rank,distance),
        .annotate(

            # Turns the text column into a searchable vector,
            search=SearchVector('chunk__text'), 

            # Computes keyword relevance score, Higher = better keyword match
            # F('search') gets the value of search! (so there is comparsinon between serach column and query value for each row)
            rank=SearchRank(F('search'), query),

            # Computes semantic distance
            distance=L2Distance('vector', input_text_embedding),
        )
        .filter(Q(chunk__document__conversation=conversation) | Q(chunk__document__is_initial=True)) # in demo case we need to filter for the current conversation + initial documents

        # Highest keyword match first (-rank) , Then best semantic similarity (distance ascending)
        .order_by('-rank', 'distance')[:num]
    )

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

    conversation = Conversation.objects.get(chat_id=telegram_object.chat_id )
    doc_object = Document.objects.create(conversation=conversation,telegram_message=telegram_object)
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
        if data == 'text':
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
            duration_threshold = 60
            duration = message_data.get('voice',{}).get('duration',{})
            if duration < duration_threshold:
                file_data = telegram_downloader(message_data['voice']['file_id'])
                django_content_file = ContentFile(file_data)
                audio_obj = AudioContent()
                audio_obj.file.save(name=f"name.oga",content=django_content_file)
                doc_source_obj = creating_document_source(audio_obj)
                doc_object.document_source = doc_source_obj
                doc_object.save()
                return doc_object
            send_message(chat_id=telegram_object.chat_id,text="Demo restrictions: Please make sure your voice duration is less than 60 seconds.")
            return False
    
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
    """
    For sending message in the conversation
    """
    logger.debug(message_sender.__name__)

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
    logger.debug(fetch_message_history.__name__)
    
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

    ragtoolkit = RetrievalToolKit(openai_model=constants.OPENAI_CHAT_MODEL)
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
    
def message_sender_custom(conversation:Conversation,message):
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
    print(entities_handling.__name__)
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

def user_message_categorizer(message:Message):
    logger.debug(user_message_categorizer.__name__)

    content = message.content
    conversation=message.conversation

    # Fetch Context
    similar_embeddings = hybrid_search(conversation=conversation,user_query=message.content,input_text=message.content , num=5)

    context =''
    if similar_embeddings:
        similar_text = "\n".join([embedding_obj.chunk.text for embedding_obj in similar_embeddings])
        context = similar_text

    # Check if the question is related
    retreival_instance = RetrievalToolKit(openai_model=constants.OPENAI_CHAT_MODEL)

    user_prompt = f"""
        User Question: {content}\n\n
        Available Information: {context}
    """
    result = retreival_instance.message_categorizer(user_prompt)
    return context,result

def process_user_message(message:Message):
    logger.debug(process_user_message.__name__)

    content = message.content
    conversation=message.conversation
    context,result = user_message_categorizer(message)
    
    # Fetch message history
    message_history = fetch_message_history(message)

    if result in [0,1]:
        logger.info("Question can be answered with available information")
        # Enough context / context not required to answer
        nlptoolkit = RetrievalToolKit(openai_model=constants.OPENAI_CHAT_MODEL)
        new_messages = {'role':'user','content':f"User question: {content}\n\nAvailable information: {context}"}

        response = nlptoolkit.openai_text_generator(message_history,new_messages)

        message_sender(
                conversation=conversation,
                content=response,
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
            print('chat id: ',chat_id)
            telegram_message_id = send_message(chat_id=chat_id,text=constants.telegram_message_support(message.conversation.user.first_name,content))

            # Updating instance (message object) with telegram id
            message.tg_id = telegram_message_id
            message.save()
            print(telegram_message_id) 
        else:
            code = message.conversation.pk
            conversation.code = code
            conversation.save()
            message_sender_custom(conversation=message.conversation,message=constants.DEMO_TELEGRAM_HUMAN_ROLE_MESSAGE)
            message_sender_custom(conversation=message.conversation,message=constants.demo_telegram_verify_messsage(code))

    elif result in [3]:
        logger.info("Question is out of scope of answering")
        # send and aswer which you can not respond to this matter
        message_sender(
                conversation=message.conversation,
                content=constants.CANT_ANSWER_MESSAGE,
                is_agent=True
                )

# !tar -czf pack.tar.gz ./
def creating_text_content_object(content:str):
    logger.debug(creating_chunk_objects.__name__)
    model_object = TextContent.objects.create(content = content)
    model_object.save()

    return model_object

def creating_document_source(model_object):
    logger.debug(creating_document_source.__name__)
    content_type_obj = ContentType.objects.get_for_model(model_object.__class__)

    doc_source_obj = DocumentSource.objects.create(
        content_type = content_type_obj, # content type object, which is linked to the actual object
        object_id = model_object.pk # the specfific id of the that actual object (not content type object)
    )

    return doc_source_obj

def creating_document_object(document_source, category="user_input", conversation=None, is_initial=False, caption=None,user_message=None,telegram_message=None) -> Document:
    logger.debug(creating_document_object.__name__)
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
    logger.debug(transcriber.__name__)
    rag_toolkit = NLPToolKit()
    return rag_toolkit.audio_to_text(document_object.document_source.content_object.file.path)

def fetch_content_from_document(document_object:Document):
    """
    This function is for getting content from document object, as document object uses content type object, it should detect which type of content is and then going for getting each content in it's own way
    """
    logger.debug(fetch_content_from_document.__name__)

    if type(document_object.document_source.content_object) is TextContent:
        logger.debug("Content type is TextContent")
        return document_object.document_source.content_object.content
    elif type(document_object.document_source.content_object) is AudioContent:
        logger.debug("Content type is AudioContent")
        if not document_object.document_source.content_object.trascription:
            logger.debug(f"file path: {document_object.document_source.content_object.file.path}")
            trascription = transcriber(document_object)
            logger.debug(f"Transcription: {trascription}")

            # saving in the database
            document_object.document_source.content_object.trascription = trascription
            document_object.save()
            # creting chunks
        return document_object.document_source.content_object.trascription
    else:
        logger.info('Document object class is not supported')
        return False

def creating_chunk_objects(document_object:Document) -> List[Chunk]:
    logger.debug(creating_chunk_objects.__name__)
    content_for_chunk = fetch_content_from_document(document_object)
    
    if content_for_chunk:

        rag_toolkit = NLPToolKit()
        chunks = rag_toolkit.split_text(text=content_for_chunk)

        objects = Chunk.objects.bulk_create(
            [
                Chunk(chunk_id = i , text = chunk , document = document_object) for i, chunk in enumerate(chunks)
            ] 
        )
        return objects

def creating_embedding_objects(chunks):
    logger.debug(creating_embedding_objects.__name__)
    
    rag_toolkit = NLPToolKit()

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
        
def add_initial_documents(conversation):
    logger.debug(f"{add_initial_documents.__name__}")
    """
    This function is for adding initial data in demo mode
    """
    document_indices = ['1']
    dir = os.path.join(settings.BASE_DIR,constants.INITIAL_DATA_DIR)
    for document_index in document_indices:
        try:
            file_path = os.path.join(dir,f'{document_index}.txt')
            with open(file_path) as text_file:
                text_string = text_file.read()
                logger.info(f"Inital data text first 50 chars: {text_string[:50]}")
                with transaction.atomic():
                    text_content_object = creating_text_content_object(content=text_string)
                    doc_source_object = creating_document_source(model_object=text_content_object)
                    doc_object = creating_document_object(conversation=conversation,document_source=doc_source_object)
                    chunk_objects = creating_chunk_objects(document_object=doc_object)
                    embedding_objects = creating_embedding_objects(chunks=chunk_objects)
                    logger.debug(f"Embedding has been created: {embedding_objects}")

                    return True

        except FileNotFoundError:
            logger.exception("File not found")

def delete_unused_conversation():

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