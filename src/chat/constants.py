INITIAL_DATA_DIR="chat/management/commands/initial_data"

# Hugging face
HF_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
HF_INFERENCE_MODEL="meta-llama/Llama-3.1-8B-Instruct"


# OpenAI
OPENAI_CHAT_MODEL="gpt-4.1-mini"

# Chunking
CHUNK_SIZE=200
CHUNK_OVERLAP=20

# Business
BUSINESS_NAME="TelBurger restaurant"
BUSINESS_DESCRIPTION="TelBurger sells burgers, so the scope you can answer is about pricing, delivery of burgers, type of burgers, refunding, and anything related to a burger restaurant customer service.\n"

# Messages
NO_INFORMATION_MESSAGE="I don't have enough info. I'll check with a human agent and get back to you soon!"
DEMO_TELEGRAM_HUMAN_ROLE_MESSAGE="The AI Agent doesn't have enough information to answer to this question, So now is trying to send a message to a human agent on Telegram. Since this is a <strong>demo</strong>, you'll play the role of the human agent yourself."
CANT_ANSWER_MESSAGE="Sorry! I can't answer to this question!"

def telegram_message_support(firstname,content):
    return f"""💬 A customer named <b>{firstname}</b> asked the following question:\n\n<blockquote>{content}</blockquote>\n\n🔻 I don't have enough information to answer it. Please reply to this message with your response so I can answer it correctly.
    """

def demo_telegram_verify_messsage(code):
    return f"""<br>Please link your Telegram account to this conversation.\n<br><br>Send number below to <ahref="https://t.me/telrag_bot">@telrag_bot</a><br><br><center><b>{code}</b></center>"""

def data_path(name:str):
    main_path = f"data/knowledge_base/{name}/"
    path_dict =  {
        "initial" : "initial_data",
        "test_raw" : "test_data/raw",
        "test_retrieval_question_jsonl" : "test_data/jsonl/retrieval_eval_question.jsonl",
        "test_retrieval_declerative_jsonl" : "test_data/jsonl/retrieval_eval_declerative.jsonl",
    }

    for i in path_dict:
        path_dict[i] = main_path + path_dict[i]

    return path_dict
     