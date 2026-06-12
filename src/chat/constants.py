INITIAL_DATA_DIR="chat/management/commands/initial_data"

# Hugging face
HF_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
HF_INFERENCE_MODEL="meta-llama/Llama-3.1-8B-Instruct"
HF_TEXT_GENERATION_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

# OpenAI
OPENAI_CHAT_MODEL="gpt-4.1-mini"
OPENAI_TRANSCRIPTION_MODEL = "whisper-1"

# Cost
# source: https://developers.openai.com/api/docs/pricing
COST_PER_TOKEN={
    OPENAI_CHAT_MODEL:{
        "unit" : 1000000,
        "currency":"usd",
        "input" : .4,
        "output" : 1.6
    },
    HF_EMBEDDING_MODEL:{
        "unit" : 1,
        "currency":"usd",
        "embedding" : 0,
    },
}

# Chunking
CHUNK_SIZE=200
CHUNK_OVERLAP=20

# Hybrid Search
BETA=0
TOP_K=10

# Business
BUSINESS_NAME="TelMart"
BUSINESS_DESCRIPTION="You are an AI Assistant for a grocery store called TelMart. You help customers with questions about products, prices, promotions, store services, and policies. You can assist with finding items, checking product availability, tracking orders, and explaining returns, refunds, and gift cards. You provide fast, accurate, and friendly support at any time. When a request requires additional help, you guide the customer to the appropriate team or resource.\n"


# Messages
NO_INFORMATION_MESSAGE="I don't have enough info. I'll check with a human agent and get back to you soon!"
DEMO_TELEGRAM_HUMAN_ROLE_MESSAGE="The AI Agent doesn't have enough information to answer to this question, So now is trying to send a message to a human agent on Telegram. Since this is a <strong>demo</strong>, you'll play the role of the human agent yourself."
CANT_ANSWER_MESSAGE="Sorry! I can't answer to this question!"

def telegram_message_support(firstname,content):
    return f"""💬 A customer named <b>{firstname}</b> asked the following question:\n\n<blockquote>{content}</blockquote>\n\n🔻 I don't have enough information to answer it. Please reply to this message with your response so I can answer it correctly.
    """

def demo_telegram_verify_messsage(code):
    return f"""<br>Please link your Telegram account to this conversation.\n<br><br>Send number below to <ahref="https://t.me/telrag_bot">@telrag_bot</a><br><br><center><b>{code}</b></center>"""

def data_path(name:str,key_path:'str'):
    main_path = f"data/knowledge_base/{name}/"
    path_dict =  {

        # Initial Data
        "initial" : "initial_data",

        # Test Files
        "test_raw" : "test_data/raw",
        "test_retrieval_question" : "test_data/jsonl/retrieval_eval_question.jsonl",
        "test_retrieval_declerative" : "test_data/jsonl/retrieval_eval_declerative.jsonl",
        "llm_eval_qa" :"test_data/jsonl/llm_eval_qa.jsonl",

        # Result files
        "ret_result" :"result/ret_result.jsonl",
        "ret_result_history" :"result/ret_result_history.jsonl",
        "llm_result" : "result/llm_result.jsonl",
        "llm_result_history" :"result/llm_result_history.jsonl",

        # Mardkdown Report
        "evaluation_report" :f"result/{name}_evaluation_report.md",

        # Plots 
        "result_plots" :"result/plots",
        "ret_plot" :"result/plots/retrieval.png",
        "ret_history_plot" :"result/plots/retrieval.png",
        "llm_plot" :"result/plots/llm.png",
        "llm_history_plot" :"result/plots/llm.png",
        "ret_plot_md" : "plots/retrieval.png",
        "llm_plot_md" : "plots/llm.png",
        "ret_history_plot_md" : "plots/retrieval.png",
        "llm_history_plot_md" : "plots/llm.png",
    }

    for i in path_dict:
        path_dict[i] = main_path + path_dict[i]

    try:
        return path_dict[key_path]
    except KeyError as e :
        print(f"Key Error in constant.data_path : The is no such a key in the dictionary : {key_path}\n")
    except FileNotFoundError as e :
        print(f"Path {main_path} is not existed\n")
     
BUSINESS_NAME_FOR_DATA = "telmart"

# Pipeline

RAG_COMPONENTS = {
    "Message Categorizer" : "message_categorizer",
    "Text Generator" : "text_generator",
    "Embedder" : "embedder",
    "Hybrid Search" : "hybrid_search",
    "Query Rewriting" : "query_rewriting",
    "Audio Transcription" : "audio_transcription"
}

RC_DETAILS = {
    RAG_COMPONENTS["Message Categorizer"] : {"model" : OPENAI_CHAT_MODEL ,"type" : "classifier" , "output" : "completion" , "job" : "Categorizing a message into preferred categories and returning the index number of the desired category."},

    RAG_COMPONENTS["Text Generator"] : {"model" : OPENAI_CHAT_MODEL ,"type" : "generator" , "output" : "list", "job" : "Responding to user query"},

    RAG_COMPONENTS["Embedder"] : {"model" : HF_EMBEDDING_MODEL ,"type" : "embedder" , "output" : "ndarray", "job" : "Converting a text to embeddings"},

    RAG_COMPONENTS["Hybrid Search"] : {"model" : None ,"type" : "search" , "output" : "queryset", "job" : "Keyword and Semantic search inside pgvector database using django ORM"},

    RAG_COMPONENTS["Query Rewriting"] : {"model" : OPENAI_CHAT_MODEL ,"type" : "rewriter" , "output" : "response", "job" : "Rewriting user query into an standard query for using in retrieval"},

    RAG_COMPONENTS["Audio Transcription"] : {"model" : OPENAI_TRANSCRIPTION_MODEL ,"type" : "transciber" , "output" : "response", "job" : "transcribing a audio file to text"},
}