# pull oficial base image
FROM python:3.9.6-alpine

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /app

# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# copy the project
COPY . /app/

ENTRYPOINT [ "gunicorn", "-p", "8000", "-w", "1", "core.asgi:application", "-k", "uvicorn.workers.UvicornWorker" ]