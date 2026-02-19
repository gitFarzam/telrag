To create a rag pipeline I have to go for modeling first, which models do I need? I need a model which have chunks and embeddings.

So, I need a postgres database with pgvector extension, but how can I handle ingestion process?

We have 2 ways, first we directly upload some documents and it will be processes and be added to the knowledge bank, category will be provided, original data with metadata, keywords, and chunks and each chunk will also have it's embeddings.

Another way is online mode, the time Ai agent can not answer to the question and will ask the admin in the telegram, admin will provide some information / taking control of chat.

By providing some data to the question, AI will store them in the database, in some way connects question and this information, information will be considered as a document with metadata, and chunks are part of the document. / processing will be handled in the background, because AI need as soon as possible use information to answer customer questions.

Admin alwys can see the q/a live from panel! and that is beautiful


## Postgres

Creaing volume

```shell
docker volume create telrag-volume
```

having variables in .env, running the container

```shell
docker run -d \
  --name telrag_db \
  --env-file .env \
  -p 5433:5432 \
  -v telrag-volume:/var/lib/postgresql/data \
  pgvector/pgvector:pg15
```

```shell
uv add psycopg2-binary #install posrgres library
uv add pgvector #pgvector library
```



Steps:

1. creating chat model
2. using form for saving in the model
3. using django channel
4. including telegram
5. creating rag models and eneabling pgvector


## Hugging face

https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client

```shell
pip install huggingface_hub
```

```python
from huggingface_hub import InferenceClient

# Set your API token as an environment variable (HF_API_TOKEN) 
# or pass it directly: token="hf_YOUR_TOKEN"
client = InferenceClient(token="hf_YOUR_TOKEN") 

# Choose an embedding model (e.g., all-MiniLM-L6-v2, which is widely used)
# A good resource for choosing models is the MTEB leaderboard: 
client.feature_extraction("Hi, who are you?")
```

## Bugs

Async and background tasks
change ai model
access to manage documents from telegram
voice parser