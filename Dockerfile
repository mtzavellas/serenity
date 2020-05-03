FROM python:3.8-slim-buster

RUN apt-get update && apt-get install --yes gcc libpq-dev

COPY $PWD/src /app
COPY $PWD/requirements.txt /app
WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app"
