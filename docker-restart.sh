echo "Docker | Pruning"
docker compose down
docker builder prune --all
docker image prune -a

echo "pulling last changes"
git pull origin demo

echo "Docker | Building"
docker compose build --no-cache
docker compose up -d