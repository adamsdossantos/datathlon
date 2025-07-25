FROM python:3.10-slim [cite: 1]

WORKDIR /app

# Instala uv
RUN pip install uv 

# Copia o requirements.txt primeiro para aproveitar o cache
COPY api/requirements.txt . 

# Instala as dependências
RUN uv pip install --system --no-cache -r requirements.txt 

# Variáveis de ambiente para o Databricks Host e Tracking URI (podem ser ENVs)
ENV MLFLOW_TRACKING_URI="databricks" [cite: 1]
ENV DATABRICKS_HOST="https://dbc-04ba26d3-c768.cloud.databricks.com/" [cite: 1]

# === SEGURANÇA: Use ARG para o token durante o build, NUNCA ENV ===
ARG DATABRICKS_TOKEN_BUILD

# Configure o token APENAS para o comando de carregamento do modelo, não como ENV persistente
RUN --mount=type=secret,id=databricks_token \
    python -c "import os, mlflow; \
    os.environ['MLFLOW_TRACKING_URI'] = os.getenv('MLFLOW_TRACKING_URI'); \
    os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST'); \
    os.environ['DATABRICKS_TOKEN'] = open('/run/secrets/databricks_token').read().strip(); \
    mlflow.set_tracking_uri('databricks'); \
    mlflow.set_registry_uri('databricks-uc'); \
    mlflow.sklearn.load_model('models:/workspace.default.tfidfvectorizer@champion'); \
    mlflow.pyfunc.load_model('models:/workspace.default.sentencetransformermodel@champion')" 

# Remova as linhas de print de variáveis de ambiente do build, elas expõem o token nos logs
# RUN python -c "import os; print('MLFLOW_TRACKING_URI:', os.getenv('MLFLOW_TRACKING_URI')); print('DATABRICKS_HOST:', os.getenv('DATABRICKS_HOST'))" 
# RUN python -c "import os; print('DATABRICKS_HOST:', os.getenv('DATABRICKS_HOST')); print('DATABRICKS_TOKEN:', os.getenv('DATABRICKS_TOKEN')); print('MLFLOW_TRACKING_URI:', os.getenv('MLFLOW_TRACKING_URI'))" 

EXPOSE 8000

# Copia os arquivos da API
COPY api/main.py . 
COPY api/utils.py . [cite: 2]

# Copia a pasta 'app' do diretório raiz do contexto de build
COPY app/ ./app [cite: 2]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] [cite: 2]