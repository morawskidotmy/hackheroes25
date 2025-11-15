FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV FLASK_APP=app.py

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--worker-class", "sync", "--timeout", "60", "app:app"]
