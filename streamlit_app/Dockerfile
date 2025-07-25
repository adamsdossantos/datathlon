FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

EXPOSE 8501

COPY app.py .
COPY pages ./pages

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
