-include .env
export

# Running app in production mode
run:
	./.sh/run.sh

down:
	docker compose down

# Running app in dev mode
run_dev:
	./.sh/run_dev.sh

down_dev:
	docker compose -f ./compose.dev.yaml down

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


	