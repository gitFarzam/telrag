```shell
uv run manage.py createsuperuser
```

## UV update lock file
```shell
uv lock --upgrade
```

## Tests

```shell
uv run manage.py test chat.tests.TestWebhook.test_if_webhook_returns_true
uv run manage.py test chat.tests.TestTelegramMessageParsing.test_processing_telegram_message
uv run manage.py test chat.tests.TestDocumentIngestion.test_processing_document
uv run manage.py test chat.tests.TestDocumentIngestion.test_proccess_chunks

uv run manage.py test chat.tests.TestRAGToolKit.test_embedding_function
uv run manage.py test chat.tests.TestRAGToolKit.test_text_generator_function

uv run manage.py test chat.tests.TestTextClassifier.test_greeting_text_classifier_function
uv run manage.py test chat.tests.TestTextClassifier.test_related_text_classifier_function
uv run manage.py test chat.tests.TestTextClassifier.test_related_question_detector
uv run manage.py test chat.tests.TestTextClassifier.test_enough_context_to_answer_detector

uv run manage.py test chat.tests.TestTelegramFileDownload.test_downloading_file
uv run manage.py test chat.tests.TestRAGToolKit.audio_transcriber
```

## Command

```shell
uv run manage.py insert_data 0
```

## github
git clone git@github.com-repo-telrag:gitfarzam/telrag.git




## Docker Commands

building containers
```shell
docker compose build --no-cache
```

running containers 
```shell
docker compose up
```

running containers in background:

```shell
docker compose up -d
```


Stop containers

```shell
docker compose down
```

View logs

```shell
docker compose logs -f
```

Open shell in Django container

```shell
docker compose exec web bash
```



chmod +x /usr/src/app/entrypoint.sh
docker rm -f telrag_pgvector telrag_redis telrag_app telrag_celery 2>/dev/null || true



```shell
docker stop telrag 
docker stop telrag_celery
docker remove telrag
docker remove telrag_celery
docker builder prune --all
docker image prune -a
```


django app image
```shell
docker build -t telrag_image .
```
django app container
```shell
docker run -d \
    -p 8006:8006 \
    --name telrag \
    --network telrag-network \
    -v $(pwd)/staticfiles:/usr/src/app/staticfiles \
    -v $(pwd)/media:/usr/src/app/media \
    telrag_image
```



Pgvector
```shell
docker run -d \
  --name telrag_container_db \
  --network telrag-network \
  --env-file .env \
  -p 5433:5432 \
  -v telrag-volume:/var/lib/postgresql/data \
  pgvector/pgvector:pg15
```



Redis
```shell
docker run -d \
--name telrag_redis \
-p 6379:6379 \
redis:latest
```


celery app image
```shell
docker build -t telrag_celery_image -f CeleryDockerfile .
```
celery app container
```shell
docker run \
  --name telrag_celery \
  --network telrag-network \
  telrag_celery_image
```