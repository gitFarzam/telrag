<<<<<<< HEAD
FROM python:3.12-slim

WORKDIR /usr/src/app

# --no-cache-dir avoids keeping pip's cache in the image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project (first dot in current dir in local:telrag/, second dot is current fir in container: /use/scr/app)
COPY . .

ENV PYTHONUNBUFFERED=1

# providing execute permission inside the container
RUN chmod +x /usr/src/app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
||||||| 6d2c1b6
=======
FROM python:3.12-slim

WORKDIR /usr/src/app

# Installing curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# --no-cache-dir avoids keeping pip's cache in the image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project (first dot in current dir in local:telrag/, second dot is current for in container: /use/scr/app)
COPY . .

ENV PYTHONUNBUFFERED=1

# providing execute permission inside the container
RUN chmod +x /usr/src/app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
>>>>>>> demo
