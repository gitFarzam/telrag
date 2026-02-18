```shell
uv run manage.py createsuperuser
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
```