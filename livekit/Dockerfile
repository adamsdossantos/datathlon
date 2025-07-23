FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

COPY livekit/requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY livekit/ .

CMD ["python", "main.py"]
