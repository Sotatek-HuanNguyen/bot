FROM python:3.11-slim

WORKDIR /app

COPY api/ ./api/
COPY bot.py ./bot.py
COPY config.py ./config.py
COPY exchange.py ./exchange.py
COPY strategy.py ./strategy.py
COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

ENV FLASK_APP=api.app
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "api/app.py"]