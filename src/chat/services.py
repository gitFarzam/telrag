# Standard Library Imports
import os
import logging
from asgiref.sync import async_to_sync
from typing import List
from datetime import timedelta
import time

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
from chat.utils.redact import Redact

# loading env variables
load_dotenv()

# Creating an instance of logging object
logger = logging.getLogger(__name__)
redact = Redact()


def hybrid_search(search_keyword:str,input_text_embedding,top_k:int,beta:float)->QuerySet[Embedding]:

    """
    hybrid search using pgvector library in postgresql database, both keyword and semantic search
    - search_keyword : The query for performing a keyword (lexical) search within the database.
    - input_text_embedding : The embedded input text used by the retriever for semantic search.
    - top_k : Number of documents to be retrieved
    - beta : a value between 0 and 1 determines the ratio between 2 kind of search, beta=0, 100% result comes from semantic search, beta=1 , 100% comes from keyword search
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

    return result.filter(chunk__document__is_initial=True)[:top_k]


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
    doc_object = Document.objects.create(telegram_message=telegram_object)
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
            if model_object:
                doc_source_obj = creating_document_source(model_object)
                doc_object.document_source = doc_source_obj
                doc_object.save()
                return doc_object
            else:
                return False

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
            send_message(chat_id=telegram_object.chat_id,text=f"Please make sure your voice duration is less than {str(duration_threshold)} seconds.")
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

            if command == '/getdocs':
                # get all documents from this user telegram id
                telegram_messages = TelegramMessage.objects.filter(chat_id = chat_id)
               
                if telegram_messages:
                    docs = Document.objects.filter(telegram_message__in = telegram_messages)
                    if docs:
                        for i,doc in enumerate(docs):
                            text = f"<strong>Document {str(i)}:</strong>\nid: <code>{doc.pk}</code>\nsummary: {fetch_content_from_document(doc)}" 
                            send_message(chat_id=chat_id,text=text , document_id=doc.pk,command=True)
                    else:
                        send_message(chat_id=chat_id,text="oOps! There is no document associated with your account!")
                    return True

def user_message_categorizer(message:Message, ragpipeline:RAGPipeline):
    """
    This method is for categorizing user messages in the conversation, like of the message is in the knowledge scope of AI assistant or not.

    the output is providing both context and the result, context comes from hybrid search (inputing user query), so instead of re-searching this context will be return alongside the result which is an integer, which ranges from 0 to 3 and each of them leads to a different flow.
    """
    dispatcher = Dispatcher(ragpipeline)

    content = message.content  

    # RAG Component
    rewrited_query = dispatcher.query_rewriter_component(content)

    # RAG Component 
    input_text_embedding = dispatcher.embedding_component(rewrited_query)

    # RAG Component 
    context = dispatcher.hybrid_search_component(content,input_text_embedding, top_k=5)

    logger.info(f"Relevant Documents from Hybrid Search: {redact.redact_text(context)}")

    # RAG Component
    result = dispatcher.message_categorizing_component('categorizing' ,content ,context)
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

    
    
    # Fetch message history
    message_history = fetch_message_history(message)

    logger.info("Message Categorizer Result",{'category_number':result})

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


        chat_id = os.getenv('TELEGRAM_ALLOWED_USER_IDS')
        
        firstname = message.conversation.user.first_name
        text = constants.telegram_message_support.format(firstname=firstname , content=content)

        telegram_message_id = send_message(chat_id=chat_id,text=text)

        # Updating instance (message object) with telegram id
        message.tg_id = telegram_message_id
        message.save()



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
    model_object = TextContent.objects.create(content = content)
    return model_object

    

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



def creating_document_object(document_source, category="user_input", is_initial=False, caption=None,user_message=None,telegram_message=None) -> Document:

    """
    This method is for creating document object
    """

    doc_object = Document.objects.create(document_source = document_source)

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
            logger.info(f"Transcription: {redact.redact_text(trascription)}")

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
                # print(f"category : {category} - filepath: {file_path}")
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
                                        number_of_documents+=1
                    else:
                        return False
                    
        return number_of_documents,embedding_objects
    except IntegrityError as e:
        print(f"IntegrityError: Unique content violation, content object should be unique, you probably are inserting similar documents into the database, Error description:\n\n\n{e}")
        logger.error(e)
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

        rag_c_dict_logging = rag_component_dict.copy()
        rag_c_dict_logging["ragpipeline"] = self.rag_pipeline.pk
        logger.info(msg="RAG Component",extra=rag_c_dict_logging)

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
    
    def hybrid_search_component(self,content:str,input_text_embedding,top_k):

        similar_embeddings = hybrid_search(search_keyword=content,input_text_embedding=input_text_embedding ,beta=constants.BETA, top_k=top_k)
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
        