-include .env
export

up:
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
	fi
		

create_admin:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | using compose.dev.yaml"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "python ./src/manage.py createsuperuser --noinput || true"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | using docker-compose.yaml"; \
		docker compose exec app bash -c "python ./src/manage.py createsuperuser --noinput || true"; \
	fi


test:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | using compose.dev.yaml"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py test"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | using docker-compose.yaml"; \
		docker compose exec app bash -c "cd src && python manage.py test"; \
	fi


insert_data:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | using compose.dev.yaml"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py insert_initial_data"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | using docker-compose.yaml"; \
		docker compose exec app bash -c "cd src && python manage.py insert_initial_data"; \
	fi


rag_eval:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | using compose.dev.yaml"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py rag_evaluation"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | using docker-compose.yaml"; \
		docker compose exec app bash -c "cd src && python manage.py rag_evaluation"; \
	fi


rag_eval_new:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | using compose.dev.yaml"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py rag_evaluation --new"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | using docker-compose.yaml"; \
		docker compose exec app bash -c "cd src && python manage.py rag_evaluation --new"; \
	fi


set_webhook:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | Setting Dev webhook (ngrok)"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py tg_webhook --set"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | Setting Production webhook"; \
		docker compose exec app bash -c "cd src && python manage.py tg_webhook --set"; \
	fi


info_webhook:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | Setting Dev webhook (ngrok)"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py tg_webhook --info"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | Setting Production webhook"; \
		docker compose exec app bash -c "cd src && python manage.py tg_webhook --info"; \
	fi


del_webhook:
	@if [ "$(DEBUG)" = "1" ]; then \
		echo "DEBUG=1 | Setting Dev webhook (ngrok)"; \
		docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py tg_webhook --del"; \
	elif [ "$(DEBUG)" = "0" ]; then \
		echo "DEBUG=0 | Setting Production webhook"; \
		docker compose exec app bash -c "cd src && python manage.py tg_webhook --del"; \
	fi