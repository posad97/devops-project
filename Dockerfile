FROM python:3.8-alpine

WORKDIR /app

RUN pip install Flask flask-session mysql-connector-python requests gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
