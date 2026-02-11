```shell
uv run manage.py createsuperuser
```

## Tests

```shell
uv run manage.py test chat.tests.TestTelegramMessageParsing.test_processing_telegram_message
uv run manage.py test chat.tests.TestDocumentIngestion.test_processing_document
```