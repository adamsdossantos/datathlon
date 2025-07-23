FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

COPY streamlit_app/requirements.txt .

RUN uv pip install --system -r requirements.txt

EXPOSE 8501

COPY streamlit_app/app.py .
COPY streamlit_app/pages ./pages

CMD ["streamlit", "run", "app.py"]
