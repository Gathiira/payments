# pull oficial base image
FROM python:3.9.6-alpine

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# copy the project
COPY . /app/

ENTRYPOINT [ "gunicorn", "-p", "8000", "-w", "1", "core.asgi:application", "-k", "uvicorn.workers.UvicornWorker" ]