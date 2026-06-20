-include .env
export

# Running app in production mode
run:
	./.sh/run.sh

# Running app in dev mode
run_dev:
	./.sh/run_dev.sh

# Creating an admin user
create_admin:
	docker compose -f ./compose.dev.yaml exec app bash -c "python ./src/manage.py createsuperuser --noinput || true"

test:
	docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py test"
insert_data:
	docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py insert_initial_data"
del_data:
	docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py del_initial_data"
rag_eval:
	docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py rag_evaluation"

rag_eval_new:
	docker compose -f ./compose.dev.yaml exec app bash -c "cd src && python manage.py rag_evaluation --new"

dev_webhook:
	./.sh/dev_webhook_setup.sh

pro_webhook:
	./.sh/pro_webhook_setup.sh


	