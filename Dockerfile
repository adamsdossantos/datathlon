# Dockerfile (na raiz do seu projeto)

FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

# Copia o requirements.txt da pasta 'api/' local
COPY api/requirements.txt ./requirements.txt

# Instala as dependências Python usando uv
RUN uv pip install --system --no-cache -r ./requirements.txt # Ajuste aqui o caminho

# Cria diretórios para modelos
RUN mkdir -p /app/models/distiluse-base-multilingual-cased-v1 /app/models/

# Copia modelos pré-baixados (Eles estão na pasta 'models/' na raiz do projeto)
COPY models/distiluse-base-multilingual-cased-v1/ /app/models/distiluse-base-multilingual-cased-v1/
COPY models/tfidf_vectorizer.pkl /app/models/tfidf_vectorizer.pkl

# Variáveis de Ambiente para MLflow (HOST e URI)
ENV MLFLOW_TRACKING_URI="databricks"
ENV DATABRICKS_HOST="https://dbc-04ba26d3-c768.cloud.databricks.com/"

EXPOSE 8000

# Copia o código da API (main.py, utils.py)
# Eles estão na pasta 'api/' local. Copia para /app/api no contêiner.
COPY api/ ./api/

# Copia a pasta 'insertion/' (está na raiz do projeto)
COPY insertion/ ./insertion/

# Copia a pasta 'app/' (está na raiz do projeto)
COPY app/ ./app/

# Comando para iniciar a API FastAPI
# "api.main:app" funcionará porque o código está em /app/api no contêiner
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]