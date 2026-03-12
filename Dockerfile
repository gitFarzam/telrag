FROM python:3.12-slim

WORKDIR /usr/src/app

# install uv
RUN pip install uv

# copy dependency files first (docker cache optimization)
COPY pyproject.toml uv.lock ./

# install dependencies
RUN uv sync --frozen --no-dev

# copy project (first dot in current dir in local:telrag/, second dot is current fir in container: /use/scr/app)
COPY . .

ENV PYTHONUNBUFFERED=1

# providing execute permission inside the container
RUN chmod +x /usr/src/app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]