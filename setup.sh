echo "Docker | Pruning"
docker compose down
docker builder prune --all
docker image prune -a

echo "Docker | Building"
chmod +x entrypoint.sh
docker compose build --no-cache
docker compose up