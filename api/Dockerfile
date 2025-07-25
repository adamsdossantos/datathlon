# api/Dockerfile

FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

# Copia o requirements.txt (que está na mesma pasta api/ que este Dockerfile)
COPY api/requirements.txt .

RUN uv pip install --system -r requirements.txt

# Cria diretórios para modelos
RUN mkdir -p /app/models/distiluse-base-multilingual-cased-v1 /app/models/

# Copia modelos pré-baixados (Eles estão um nível ACIMA da pasta 'api/')
COPY ../models/distiluse-base-multilingual-cased-v1/ /app/models/distiluse-base-multilingual-cased-v1/
COPY ../models/tfidf_vectorizer.pkl /app/models/tfidf_vectorizer.pkl

# Variáveis de Ambiente para MLflow (HOST e URI)
ENV MLFLOW_TRACKING_URI="databricks"
ENV DATABRICKS_HOST="https://dbc-04ba26d3-c768.cloud.databricks.com/"

EXPOSE 8000

# Copia o código da API (main.py, utils.py)
# Eles estão na mesma pasta 'api/' que este Dockerfile
COPY api/main.py ./api/
COPY api/utils.py ./api/

# Add this line to copy the insertion directory
COPY ../insertion/ ./insertion/

# Copia a pasta 'app/'
# Ela está um nível ACIMA da pasta 'api/'
COPY ../app/ ./app/

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]