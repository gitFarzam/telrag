```shell
uv run manage.py createsuperuser
```

## Tests

```shell
uv run manage.py test chat.tests.TestWebhook.test_if_webhook_returns_true
uv run manage.py test chat.tests.TestTelegramMessageParsing.test_processing_telegram_message
uv run manage.py test chat.tests.TestDocumentIngestion.test_processing_document
uv run manage.py test chat.tests.TestRAGToolKit.test_embedding_function
uv run manage.py test chat.tests.TestRAGToolKit.test_proccess_chunks

```