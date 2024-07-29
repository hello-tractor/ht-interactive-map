FROM python:3.12-slim

COPY . .

RUN pip3 install -r requirements.txt

RUN gunicorn -w 17 -b 127.0.0.1:80 app:app