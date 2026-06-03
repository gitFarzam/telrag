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
  --network telrag-network \
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
5. creating rag models and enabling pgvector


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
webhook line of requests when stack at the top of each other
integration of functions, seprating some others
uploading in github


## Telegram
Submit webhook
Submit secret (posting through set_telegram_webhook_secret function)
-> note: probably just the set_telegram_webhook_secret functions do both

-> time for sending messages
-> in demo , time should be by detecting the telegram messages from chat id, so a chat id should be placed as a new field in the model
-> later if there is a background task it should not process


## Document
-> filter for documents

## Prmompts:

async inside task: @src/chat/tasks.py:15-22 @src/chat/services.py:230 @src/chat/services.py:206-209  I have a celery task : task_reply_message ,, which contains multiple functions, all of them works , but there is a problem with of them, one of them is agent_message_sender function, inside that there is a function: message_sender , inside message_sender , there is a functinality: @services.py (206-209) this functoinality does not work, I need to keep celery task and I need this functionality which is for sending messsage to a channel layer works, to receive the message live in the front

## UI
blocking sending new message when there is a process underhood (I have to be notified when celery task is running so while running sending new messages should be blocked, and when is finished it should be open again)


## Celery
a cronjob for deleting conversations after 24h, also check at least is should spend 1 day from creation


## Docker compose

note that docker compose automatically creates a network, so we have to get the name of it and then connect caddy to it.
```shell
<project_name>_default
```

As repo is mounted, I can, or to say have to run this out of the run, a setup.sh file can fix the issue
```shell
chmod +x entrypoint.sh
```


## General
- Adding an admin with a custom login address.
- Improving integration with OpenAI.
- Enhancing error handling.
- Limiting voice message length.
- Added a delete option in the chat view.
- Fixed WebSocket issues in mobile view by using wss:// instead of ws:// (testing can be done in online mode via HTTPS).
- Added functionality to handle irrelevant questions, such as "I need to take a shower!", ensuring the AI agent cannot answer them.
- Avoided long voice messages.
- Clarified that if you send a text or voice message without replying, it will be stored separately as context.
- Edited messages that are instantly sent after verification to include descriptions.
- Fixed the combination of user Telegram messages and responses.
- Added an additional guide explaining that if you open multiple browsers, your messages will go to different conversations; clicking /refresh connects you to the current chat.
- Added a contact form.
- Added a note that this demo may have issues in mobile view and recommends using desktop view.
- Cleaned imports, removed redundant functions, constants, fixed typos, improved logger usage, removed redundant files, updated .gitignore, and cleared git cache.
- Developed a niche app targeting a specific industry.
- Added log files compatible with the Docker logs command.
- Integrated Prometheus metrics for Docker containers (cAdvisor and Node Exporter).
- Optimized loading of initial data by having it ready in the database.
- Configured a production monitoring system limited to the Django app and app metrics using Alloy and Loki, including a secondary Alloy+/Loki config file.
- Noted that service_name is already included in Alloy outputs, which overlaps with the container_name label.
- Implemented drawing canvases for TelRAG.
- Documented how to clean older data in log and metrics storage, including retention policies in Loki and Prometheus.
- Adding a "Keep my conversation" button, allowing users to retain their conversations and retrieve their username and password.
- Added documentation for using ngrok in development mode.
- Fixing ‍`DOCKER‍‍` and `DEBUG` environment variables and database connection issues in development mode.
- Adding caching.
- Changing the port from 8006 to 8000!
- RAG pipeline dispatcher


## Security
- Opening ports for grafana and flower panels can be closed probably, as caddy is using internal network for exposing
- Safe db quieris
- managing log storage in loki! Alloy scraping and prometheus!
- Create Alert in grafana
- Limit container memory usage
- Limit receving messages in telegram for each chat id - maximum 100, increase 3 seconds waiting to 5 seconds
- Where celery tasks results are stored in flower? they should not stack on the top of each other

Copilot: command + control + i

## RAG
- Retrieval Evaluation
- LLM Evaluation
- Query Re-Writing
- Caching
- Check Ipad!
- Streaming Large JsonL files in json reader (!Important to also explain it in linkedin!)

## SQL
- Duplicated queries