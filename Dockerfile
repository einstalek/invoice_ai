FROM python:3.11-slim

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_COLLECTSTATIC=1 python manage.py collectstatic --noinput

EXPOSE 8000

CMD gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 300 --workers 2
