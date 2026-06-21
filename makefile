-include .env
export

run:
	@if [ "$(DEBUG)" = "1" ] && [ "$(PUBLIC)" = "0" ]; then \
		echo "DEBUG=1 PUBLIC=0 | Development Version | compose.dev.yaml will be used to run the program. | Some features, such as receiving messages from Telegram, may not work."; \
		./.sh/run_dev.sh; \
	elif [ "$(DEBUG)" = "1" ] && [ "$(PUBLIC)" = "1" ]; then \
		echo "DEBUG=1 PUBLIC=1 | Development Version | compose.dev.yaml will be used to run the program.  | ngrok will PUBLISH your application throught the internet"; \
		./.sh/run_dev_public.sh; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | Production Version | docker-compose.yaml will be used to run the program. "; \
		./.sh/run.sh; \
	else \
		echo "Error: Incorrect Values | DEBUG = $(DEBUG) PUBLIC = $(PUBLIC)"; \
		echo "The correct values for DEBUG and PUBLIC are 0 or 1."; \
	fi

down:
	@if [ "$(DEBUG)" = "1" ] && [ "$(PUBLIC)" = "0" ]; then \
		echo "DEBUG=1 PUBLIC=0 | Stopping compose.dev.yaml"; \
		docker compose -f ./compose.dev.yaml down; \
	elif [ "$(DEBUG)" = "1" ] && [ "$(PUBLIC)" = "1" ]; then \
		echo "DEBUG=1 PUBLIC=1 | Stopping compose.dev.yaml (+ ngrok service)"; \
		docker compose -f ./compose.dev.yaml --profile public down; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | Stopping docker-compose.yaml"; \
		docker compose down; \
	else \
		echo "Error: Incorrect Values | DEBUG = $(DEBUG) PUBLIC = $(PUBLIC)"; \
		

# Creating an admin user
create_admin:
	docker compose exec app bash -c "python ./src/manage.py createsuperuser --noinput || true"

test:
	docker compose exec app bash -c "cd src && python manage.py test"
insert_data:
	docker compose exec app bash -c "cd src && python manage.py insert_initial_data"
del_data:
	docker compose exec app bash -c "cd src && python manage.py del_initial_data"
rag_eval:
	docker compose exec app bash -c "cd src && python manage.py rag_evaluation"

rag_eval_new:
	docker compose exec app bash -c "cd src && python manage.py rag_evaluation --new"

set_webhook:
	./.sh/pro_webhook_setup.sh

dev_set_webhook:
	./.sh/dev_webhook_setup.sh

echo "The correct values for DEBUG and PUBLIC are 0 or 1."; \
	fi