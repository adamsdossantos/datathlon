FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

COPY api/requirements.txt .

RUN uv pip install --system -r requirements.txt

EXPOSE 8000

COPY api/main.py .
COPY api/utils.py .
COPY app ./app
COPY insertion ./insertion
COPY data ./data

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
